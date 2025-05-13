from datetime import datetime, timedelta
import secrets
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import uuid
from models.NewAppMetadataModel import NewAppMetadataModel
from models.AppMetadataModel import AppMetadataModel
from models.UpdateAppMetadataMode import UpdateAppMetadataModel
from schemas.UnverifiedAdminUserModel import UnverifiedAdminUserModel
from utils.database import db

from models.AdminCredentialsModel import AdminCredentialsModel
from utils.email import send_email
import utils.exception as exception
from schemas.AdminUserModel import AdminUserModel
from utils.auth import generate_token, get_current_user, hash
import utils.success as success

ADMIN_ALLOWED_LOGIN_ATTEMPTS = 3
ADMIN_ACCESS_TOKEN_EXP_MINS = 10
ADMIN_REFRESH_TOKEN_EXP_MINS = 60

admin_col = db.admin

admin_router = APIRouter()


# Unprotected routes

@admin_router.post("/admin/login")
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
        max_age=access_token_exp
    )
    res.set_cookie(
        "refresh_token", 
        refresh_token,
        httponly=True,
        samesite="strict",
        max_age=refresh_token_exp
    )

    return { "message": "User authenticated" }

@admin_router.post("/admin/register")
def admin_register(body: AdminCredentialsModel):
    user_exist = admin_col.find_one({ "email": body.email }) is not None

    if (user_exist):
        return exception.data_conflict("Email already used.")
    
    verification_code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    message = f"You verification code is {verification_code}"
    send_email("Warden", body.email, message)

    new_admin_user = UnverifiedAdminUserModel(**{
        "email": body.email,
        "hash": hash(body.hash),
        "apps": {},
        "login_attempts": 0,
        "account_verified": False,
        "verification_code": verification_code
    })

    admin_col.insert_one(new_admin_user.model_dump())

    return { "message": "Unverified account has been registered" }

@admin_router.get("/admin/logout")
def admin_logout(res: Response):
    res.delete_cookie(key="access_token")
    res.delete_cookie(key="refresh_token")

    return { "message": "User logged out" }


# Protected routes

@admin_router.post("/admin/app/{app_name}")
def admin_register_app(app_name: str, body: NewAppMetadataModel, user: AdminUserModel = Depends(get_current_user)):
    if (app_name in user.apps):
        return exception.data_conflict("App already exists.")
    
    new_app = body.model_dump(exclude=["name"])
    new_app.update({ "api_key_hash": "" })
    
    updated_apps: dict = user.model_dump()["apps"]
    updated_apps.update({ app_name: new_app })
    
    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "message": f"{app_name} has been registered."}

@admin_router.put("/admin/app/{app_name}")
def admin_update_app(body: UpdateAppMetadataModel, app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (app_name not in user.apps):
        return exception.data_conflict("App doesn't exist.")
    
    updated_apps: dict = user.model_dump()["apps"]
    del updated_apps[app_name]
    
    updated_app = body.model_dump(exclude=["name"])
    updated_app.update({ "api_key_hash": "" })
    
    updated_apps.update({ body.name: updated_app })
    
    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "message": f"{app_name} has been updated."}

@admin_router.get("/admin/app/{app_name}/generate_api_key")
def admin_generate_api_key(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (app_name not in user.apps):
        return exception.data_conflict("App doesn't exist.")
    
    api_key = hash(str(uuid.uuid4()))

    updated_apps: dict = user.model_dump()["apps"]
    updated_apps[app_name]["api_key_hash"] = hash(api_key)

    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "api_key": api_key }

@admin_router.delete("/admin/app/{app_name}")
def admin_delete_app(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (app_name not in user.apps):
        return exception.data_conflict("App doesn't exist.")

    updated_apps: dict = user.model_dump()["apps"]
    del updated_apps[app_name]

    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "message": f"{app_name} deleted successfully." }
