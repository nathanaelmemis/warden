from datetime import datetime, timedelta
import secrets
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, Response
from models import Admin, UnverifiedAdmin
from schemas import AppCreate, AppInsert, AppResponse, AppUpdate, ChangePassword, Credentials, VerificationCode
from database import db
from utils.logging import logger

from utils.email import send_verification_email
import utils.exception as exception
from auth import generate_api_key, generate_token, get_current_admin, hash
import utils.success as success

ADMIN_ALLOWED_LOGIN_ATTEMPTS = 3
ADMIN_ACCESS_TOKEN_EXP_SECS = 10 * 60
ADMIN_REFRESH_TOKEN_EXP_SECS = 60 * 60

admin_col = db.admin
app_col = db.app

admin_router = APIRouter()


# Unprotected routes

# Admin Account

@admin_router.post("/admin/login", tags=["Admin Account"])
def admin_login(credentials: Credentials, res: Response):
    admin: dict = admin_col.find_one({ "email": credentials.email })

    if (not admin):
        raise exception.invalid_credentials

    if (admin.get("verification_code")):
        raise exception.account_not_verified
    
    admin: Admin = Admin(**admin)

    if (admin.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        raise exception.account_locked
    
    double_hash = hash(credentials.hash)

    if (double_hash != admin.hash):
        # increment login attempts
        admin_col.update_one({ 
            "_id": ObjectId(admin.id) 
        }, { 
            "$set": { "login_attempts": admin.login_attempts + 1 }
        })
        raise exception.invalid_credentials

    # reset login attempts
    admin_col.update_one({ 
        "_id": ObjectId(admin.id) 
    }, { 
        "$set": { "login_attempts": 0 }
    })
    
    access_token_exp = datetime.utcnow() + timedelta(seconds=ADMIN_ACCESS_TOKEN_EXP_SECS)
    refresh_token_exp = datetime.utcnow() + timedelta(seconds=ADMIN_REFRESH_TOKEN_EXP_SECS)

    access_token_data = admin.model_dump(exclude={"hash"})
    refresh_token_data = { "_id": admin.id }
    
    access_token = generate_token(access_token_data, access_token_exp)
    refresh_token = generate_token(refresh_token_data, refresh_token_exp)
    
    res.set_cookie(
        "access_token", 
        access_token,
        httponly=True,
        samesite="strict",
        max_age=ADMIN_ACCESS_TOKEN_EXP_SECS,
    )
    res.set_cookie(
        "refresh_token", 
        refresh_token,
        httponly=True,
        samesite="strict",
        max_age=ADMIN_REFRESH_TOKEN_EXP_SECS,
    )

    logger.info(f"Admin {admin.id} authenticated.")
    # can't use success.ok() becase cookies will not be included breaking the endpoint.
    return { "message": "Admin authenticated." }

@admin_router.post("/admin/register", tags=["Admin Account"])
def admin_register(credentials: Credentials):

    user_exist = admin_col.find_one({ "email": credentials.email }) is not None

    if (user_exist):
        raise exception.data_conflict("Email already used.")
    
    verification_code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    # TODO: Add link to frontend
    message = f"You verification code is {verification_code}"

    send_verification_email("Warden", credentials.email, message)

    user_id = admin_col.insert_one({
            "email": credentials.email,
            "hash": hash(credentials.hash),
            "apps": [],
            "login_attempts": 0,
            "verification_code": verification_code
        }).inserted_id

    logger.info(f"Admin {str(user_id)} registered successfully.")
    return success.created(str(user_id))

@admin_router.get("/admin/logout", tags=["Admin Account"])
def admin_logout(res: Response):
    res.delete_cookie(key="access_token")
    res.delete_cookie(key="refresh_token")

    # can't use success.ok() becase cookies removal will not be included breaking the endpoint.
    return { "message": "Admin logged out." }

@admin_router.post("/admin/{admin_id}/verify", tags=["Admin Account"])
def verify_account(body: VerificationCode, admin_id: str):
    admin = admin_col.find_one({ "_id": ObjectId(admin_id) })

    if (not admin):
        raise exception.invalid_credentials

    admin = UnverifiedAdmin(**admin)
    
    if (admin.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        raise exception.account_locked
    
    if (body.verification_code != admin.verification_code):
        # increment login attempts when wrong password
        admin_col.update_one({ 
                "_id": ObjectId(admin.id) 
            }, { 
                "$set": { "login_attempts": admin.login_attempts + 1 }
            })

    admin_col.update_one({ 
            "_id": ObjectId(admin.id) 
        }, { 
            "$set": { 
                "login_attempts": 0,
            },
            "$unset": {
                "verification_code": ""
            }
        })

    logger.info(f"Admin {admin.id} was verified.")
    return success.ok("Account verified successfully.")

# Protected routes

# Admin Account

@admin_router.get("/admin", tags=["Admin Account"], response_model=Admin, response_model_exclude={"hash", "login_attempts"})
def get_admin(admin: Admin = Depends(get_current_admin)):
    return admin

@admin_router.delete("/admin", tags=["Admin Account"])
def delete_admin(admin: Admin = Depends(get_current_admin)):
    admin_col.delete_one({ "_id": ObjectId(admin.id) })

    return success.ok("Account deleted successfully.")

@admin_router.patch("/admin/changepassword", tags=["Admin Account"])
def change_password(body: ChangePassword, admin: Admin = Depends(get_current_admin)):
    double_hash = hash(body.hash)
    if (double_hash != admin.hash):
        raise exception.invalid_credentials
    
    double_new_hash = hash(body.new_hash)
    admin_col.update_one({
            "_id": ObjectId(admin.id)
        }, {
            "$set": { "hash": double_new_hash }
        })

    logger.info(f"Admin {admin.id} successfully changed password.")
    return success.ok("Password changed successfully.")

# Admin Apps

@admin_router.get("/admin/app", tags=["Admin Apps"], response_model=List[AppResponse])
def get_registered_apps(admin: Admin = Depends(get_current_admin)):
    app_ids = [ ObjectId(app_id) for app_id in admin.apps ]
    return app_col.find({ "_id": { "$in": app_ids }}).to_list()

@admin_router.post("/admin/app", tags=["Admin Apps"])
def admin_register_app(app: AppCreate, admin: Admin = Depends(get_current_admin)):
    app_ids = [ ObjectId(app_id) for app_id in admin.apps ]
    app_exist = app_col.find_one({ "_id": { "$in": app_ids }, "name": app.name })
    if (app_exist):
        raise exception.data_conflict("App already exists.")
    
    app: AppInsert = AppInsert(**app.model_dump(), api_key_hash="")

    app_id: str = app_col.insert_one(app.model_dump()).inserted_id

    # create collection for new app
    db.create_collection(f"app_{app_id}")

    # update admin apps
    admin_col.update_one(
            { "_id": ObjectId(admin.id) }, 
            { "$push": { "apps": app_id }}
        )

    logger.info(f"Admin {admin.id} registered app {app_id}.")
    return success.created(str(app_id))

@admin_router.patch("/admin/app/{app_id}", tags=["Admin Apps"])
def admin_update_app(app: AppUpdate, app_id: str, admin: Admin = Depends(get_current_admin)):
    if (app_id not in admin.apps):
        raise exception.data_conflict("App doesn't exist.")

    app_col.update_one(
            { "_id": ObjectId(app_id) }, 
            { "$set": app.model_dump() }
        )

    logger.info(f"Admin {admin.id} updated app {app_id}.")
    return success.ok(f"App {app_id} has been updated.")

@admin_router.get("/admin/app/{app_id}/generate_api_key", tags=["Admin Apps"], response_model=str)
def admin_generate_api_key(app_id: str, admin: Admin = Depends(get_current_admin)):
    if (app_id not in admin.apps):
        raise exception.data_conflict("App doesn't exist.")

    api_key = generate_api_key()
    api_key_hash = hash(api_key)

    app_col.update_one(
            { "_id": ObjectId(app_id) }, 
            { "$set": { "api_key_hash": api_key_hash }}
        )

    logger.info(f"Admin {admin.id} generated API key for app {app_id}.")
    return success.ok(api_key)

@admin_router.delete("/admin/app/{app_id}", tags=["Admin Apps"])
def admin_delete_app(app_id: str, admin: Admin = Depends(get_current_admin)):
    if (app_id not in admin.apps):
        raise exception.data_conflict(f"App {app_id} doesn't exist.")

    db[f"app_{app_id}"].drop()

    app_col.delete_one({ "_id": ObjectId(app_id)})

    admin_col.update_one(
            { "_id": ObjectId(admin.id) }, 
            {"$pull": { "apps": ObjectId(app_id) }}, 
        )

    logger.info(f"Admin {admin.id} deleted app {app_id}.")
    return success.ok(f"App {app_id} deleted.")
