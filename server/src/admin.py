from datetime import datetime, timedelta
import secrets
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import uuid
from models.AppMetadataModel import AppMetadataModel
from models.UnverifiedAdminCredentialsModel import UnverifiedAdminCredentialsModel
from utils.common import app_exist, filter_out_app, get_app, model_list_dump
from utils.database import db
import os

from models.AdminCredentialsModel import AdminCredentialsModel
from utils.email import send_verification_email
import utils.exception as exception
from schemas.AdminUserModel import AdminUserModel
from utils.auth import generate_api_key, generate_token, get_current_user, hash
import utils.success as success

ADMIN_ALLOWED_LOGIN_ATTEMPTS = 3
ADMIN_ACCESS_TOKEN_EXP_MINS = 10
ADMIN_REFRESH_TOKEN_EXP_MINS = 60

admin_col = db.admin

admin_router = APIRouter()


# Unprotected routes

@admin_router.post("/admin/login", tags=["Admin Account"])
def admin_login(body: AdminCredentialsModel, res: Response):
    user = admin_col.find_one({ "email": body.email })

    if (not user):
        return exception.invalid_credentials

    user = AdminUserModel(**user)
    
    if (user.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        return exception.account_locked
    
    double_hash = hash(body.hash)
    if (double_hash != user.hash):
        # increment login attempts when wrong password
        admin_col.update_one({ 
                "_id": ObjectId(user.id) 
            }, { 
                "$set": { "login_attempts": user.login_attempts + 1 }
            })
        return exception.invalid_credentials
    
    # reset login attempts when authenticated
    admin_col.update_one({ 
            "_id": ObjectId(user.id) 
        }, { 
            "$set": { "login_attempts": 0 }
        })
    
    access_token_exp = datetime.utcnow() + timedelta(minutes=ADMIN_ACCESS_TOKEN_EXP_MINS)
    refresh_token_exp = datetime.utcnow() + timedelta(minutes=ADMIN_ACCESS_TOKEN_EXP_MINS)

    access_token_data = user.model_dump(exclude={"hash"})
    refresh_token_data = { "_id": user.id }
    
    access_token = generate_token(access_token_data, access_token_exp)
    refresh_token = generate_token(refresh_token_data, refresh_token_exp)
    
    res.set_cookie(
        "access_token", 
        access_token,
        httponly=True,
        samesite="strict",
        max_age=access_token_exp,
    )
    res.set_cookie(
        "refresh_token", 
        refresh_token,
        httponly=True,
        samesite="strict",
        max_age=refresh_token_exp,
    )

    return { "message": "User authenticated" }

@admin_router.post("/admin/register", tags=["Admin Account"])
def admin_register(body: AdminCredentialsModel):
    user_exist = admin_col.find_one({ "email": body.email }) is not None

    if (user_exist):
        return exception.data_conflict("Email already used.")
    
    verification_code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    message = f"You verification code is {verification_code}"
    send_verification_email("Warden", body.email, message)

    admin_col.insert_one({
        "email": body.email,
        "hash": hash(body.hash),
        "apps": {},
        "login_attempts": 0,
        "verification_code": verification_code
    })

    return { "message": "Unverified account has been registered" }

@admin_router.post("/admin/verify", tags=["Admin Account"])
def verify_account(body: UnverifiedAdminCredentialsModel):
    user = admin_col.find_one({ "email": body.email })

    if (not user):
        return exception.invalid_credentials

    user = AdminUserModel(**user)
    
    if (user.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        return exception.account_locked
    
    double_hash = hash(body.hash)
    if (double_hash != user.hash):
        # increment login attempts when wrong password
        admin_col.update_one({ 
                "_id": ObjectId(user.id) 
            }, { 
                "$set": { "login_attempts": user.login_attempts + 1 }
            })
        return exception.invalid_credentials
    
    

@admin_router.get("/admin/logout", tags=["Admin Account"])
def admin_logout(res: Response):
    res.delete_cookie(key="access_token")
    res.delete_cookie(key="refresh_token")

    return { "message": "User logged out" }


# Protected routes

@admin_router.get("/admin/app", tags=["Admin Apps"], response_model=List[AppMetadataModel])
def admin_register_app(user: AdminUserModel = Depends(get_current_user)):
    return user.apps

@admin_router.post("/admin/app", tags=["Admin Apps"])
def admin_register_app(app: AppMetadataModel, user: AdminUserModel = Depends(get_current_user)):
    if (app_exist(app, user.apps)):
        return exception.data_conflict("App already exists.")
    
    user.apps.append(app)
    
    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": model_list_dump(user.apps) }})

    return { "message": f"{app.name} has been registered."}

@admin_router.put("/admin/app/{app_name}", tags=["Admin Apps"])
def admin_update_app(app: AppMetadataModel, app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        return exception.data_conflict("App doesn't exist.")
    
    filtered_user_apps = filter_out_app(app_name, user.apps)
    filtered_user_apps.append(app)
    
    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": model_list_dump(filtered_user_apps) }})

    return { "message": f"{app_name} has been updated."}

@admin_router.get("/admin/app/{app_name}/generate_api_key", tags=["Admin Apps"])
def admin_generate_api_key(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        return exception.data_conflict("App doesn't exist.")
    
    filtered_user_apps = filter_out_app(app_name, user.apps)

    app = get_app(app_name, user.apps)
    api_key = generate_api_key()
    app.api_key_hash = hash(api_key)

    filtered_user_apps.append(app)

    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": model_list_dump(filtered_user_apps) }})

    return { "api_key": api_key }

@admin_router.delete("/admin/app/{app_name}", tags=["Admin Apps"])
def admin_delete_app(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        return exception.data_conflict("App doesn't exist.")

    filtered_user_apps = filter_out_app(app_name, user.apps)

    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": model_list_dump(filtered_user_apps) }})

    db[f"app_{user.id}_{app_name}"].drop()

    return { "message": f"{app_name} deleted successfully." }
