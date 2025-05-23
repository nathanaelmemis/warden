from datetime import datetime, timedelta
import secrets
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import uuid
from models.AppMetadataModel import AppMetadataModel
from models.ChangePasswordModel import ChangePasswordModel
from models.UnverifiedAdminCredentialsModel import UnverifiedAdminCredentialsModel
from schemas.UnverifiedAdminUserModel import UnverifiedAdminUserModel
from utils.common import app_exist, filter_out_app, get_app, model_list_dump
from utils.database import db
from utils.logging import logger
from pymongo.errors import PyMongoError

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

# Admin Account

@admin_router.post("/admin/login", tags=["Admin Account"])
def admin_login(body: AdminCredentialsModel, res: Response):
    user = admin_col.find_one({ "email": body.email })

    if (not user):
        raise exception.invalid_credentials

    if (user.get("verification_code")):
        raise exception.account_not_verified

    user = AdminUserModel(**user)
    
    if (user.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        raise exception.account_locked
    
    double_hash = hash(body.hash)
    if (double_hash != user.hash):
        # increment login attempts when wrong password
        admin_col.update_one({ 
                "_id": ObjectId(user.id) 
            }, { 
                "$set": { "login_attempts": user.login_attempts + 1 }
            })
        raise exception.invalid_credentials
    
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
        raise exception.data_conflict("Email already used.")
    
    # TODO: Add link to frontend
    
    verification_code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    message = f"You verification code is {verification_code}"
    send_verification_email("Warden", body.email, message)

    user_id = admin_col.insert_one({
        "email": body.email,
        "hash": hash(body.hash),
        "apps": [],
        "login_attempts": 0,
        "verification_code": verification_code
    })

    return { "message": str(user_id.inserted_id) }

@admin_router.get("/admin/logout", tags=["Admin Account"])
def admin_logout(res: Response):
    res.delete_cookie(key="access_token")
    res.delete_cookie(key="refresh_token")

    return { "message": "User logged out" }

@admin_router.post("/admin/{user_id}/verify", tags=["Admin Account"])
def verify_account(body: UnverifiedAdminCredentialsModel, user_id: str):
    user = admin_col.find_one({ "_id": ObjectId(user_id) })

    if (not user):
        raise exception.invalid_credentials

    user = UnverifiedAdminUserModel(**user)
    
    if (user.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        raise exception.account_locked
    
    if (body.verification_code != user.verification_code):
        # increment login attempts when wrong password
        admin_col.update_one({ 
            "_id": ObjectId(user.id) 
        }, { 
            "$set": { "login_attempts": user.login_attempts + 1 }
        })
        raise exception.invalid_credentials
    
    admin_col.update_one({ 
        "_id": ObjectId(user.id) 
    }, { 
        "$set": { 
            "login_attempts": 0,
        },
        "$unset": {
            "verification_code": ""
        }
    })

    return { "message": "Account verified successfully."}

# Protected routes

# Admin Account

@admin_router.get("/admin", tags=["Admin Account"], response_model=AdminUserModel, response_model_exclude={"hash", "login_attempts"})
def get_user(user: AdminUserModel = Depends(get_current_user)):
    return user

@admin_router.patch("/admin/changepassword", tags=["Admin Account"])
def change_password(body: ChangePasswordModel, user: AdminUserModel = Depends(get_current_user)):
    double_hash = hash(body.hash)
    if (double_hash != user.hash):
        raise exception.invalid_credentials
    
    double_new_hash = hash(body.new_hash)
    admin_col.update_one({
        "_id": ObjectId(user.id)
    }, {
        "$set": { "hash": double_new_hash }
    })

    return { "message": "Password changed successfully."}

# Admin Apps

@admin_router.get("/admin/app", tags=["Admin Apps"], response_model=List[AppMetadataModel])
def get_registered_apps(user: AdminUserModel = Depends(get_current_user)):
    return user.apps

@admin_router.post("/admin/app", tags=["Admin Apps"])
def admin_register_app(app: AppMetadataModel, user: AdminUserModel = Depends(get_current_user)):
    if (app_exist(app.name, user.apps)):
        raise exception.data_conflict("App already exists.")
    
    if (app.api_key_hash != None):
        raise exception.bad_request("Manual setting of api key is not allowed.")
    
    try:
        app.api_key_hash = ""

        # create collection for new app
        db.create_collection(f"app_{user.id}_{app.name}")

        # update user apps
        admin_col.update_one({ "_id": ObjectId(user.id) }, { "$push": { "apps": app.model_dump() }})

        logger.info(f"App {app.name} registered - User {user.id}")
    except:
        logger.error(f"App {app.name} cannot be registered - User {user.id}")
        logger.debug({ "app": app.model_dump() })
        logger.debug({ "user.apps": model_list_dump(user.apps) })
        raise exception.data_conflict(f"App {app.name} cannot be registered.")

    return { "message": f"{app.name} has been registered."}

@admin_router.put("/admin/app/{app_name}", tags=["Admin Apps"])
def admin_update_app(app: AppMetadataModel, app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        raise exception.data_conflict("App doesn't exist.")
    
    
    if (app.api_key_hash != None):
        raise exception.bad_request("Manual setting of api key is not allowed.")

    try:
        # if changing name, rename collection
        if (app.name != app_name):
            db[f"app_{user.id}_{app_name}"].rename(f"app_{user.id}_{app.name}")

        admin_col.update_one(
            { "_id": ObjectId(user.id) }, 
            {"$set": { 
                "apps.$[elem].name": app.name,
                "apps.$[elem].access_token_exp_sec": app.access_token_exp_sec,
                "apps.$[elem].refresh_token_exp_sec": app.refresh_token_exp_sec,
                "apps.$[elem].max_login_attempts": app.max_login_attempts,
                "apps.$[elem].lockout_time_per_attempt_sec": app.lockout_time_per_attempt_sec
            }}, 
            array_filters=[{"elem.name": app_name}]
        )

        logger.info(f"App {app.name} updated - User {user.id}")
    except:
        logger.error(f"App {app.name} cannot be updated - User {user.id}")
        logger.debug({ "app": app.model_dump() })
        logger.debug({ "user.apps": model_list_dump(user.apps) })
        raise exception.data_conflict(f"App {app.name} cannot be updated.")

    return { "message": f"{app_name} has been updated."}

@admin_router.get("/admin/app/{app_name}/generate_api_key", tags=["Admin Apps"])
def admin_generate_api_key(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        raise exception.data_conflict("App doesn't exist.")

    try:
        api_key = generate_api_key()
        api_key_hash = hash(api_key)

        admin_col.update_one(
            { "_id": ObjectId(user.id) }, 
            {"$set": { 
                "apps.$[elem].api_key_hash": api_key_hash,
            }}, 
            array_filters=[{"elem.name": app_name}]
        )

        logger.info(f"Generate API key for app {app_name} - User {user.id}")
    except:
        logger.error(f"Cannot generate API key for app {app_name} - User {user.id}")
        logger.debug({ "user.apps": model_list_dump(user.apps) })
        raise exception.data_conflict(f"Cannot generate API key for app {app_name}.")

    return { "api_key": api_key }

@admin_router.delete("/admin/app/{app_name}", tags=["Admin Apps"])
def admin_delete_app(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        logger.debug("I'm in here")
        raise exception.data_conflict(f"App {app_name} doesn't exist.")

    try:
        db[f"app_{user.id}_{app_name}"].drop()

        admin_col.update_one(
            { "_id": ObjectId(user.id) }, 
            {"$pull": { "apps": { "name": app_name }}}, 
        )

        logger.info(f"App {app_name} deleted - User {user.id}")
    except PyMongoError as error:
        logger.debug(repr(error))
        raise exception.data_conflict(f"App {app_name} cannot be deleted.")
    except:
        logger.error(f"App {app_name} cannot be deleted - User {user.id}")
        logger.debug({ "user.apps": model_list_dump(user.apps) })
        raise exception.data_conflict(f"App {app_name} cannot be deleted.")

    return { "message": f"App {app_name} deleted." }
