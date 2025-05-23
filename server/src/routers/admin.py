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
from utils.common import app_exist, model_list_dump, try_except
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
    user = try_except(
        lambda: admin_col.find_one({ "email": body.email }),
        "A MongoDB error occured.",
        body=body
    )

    if (not user):
        raise exception.invalid_credentials

    if (user.get("verification_code")):
        raise exception.account_not_verified
    
    user: AdminUserModel = try_except(
        lambda: AdminUserModel(**user),
        "Invalid admin user data from DB.",
        user=user
    )

    if (user.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        raise exception.account_locked
    
    double_hash = hash(body.hash)

    if (double_hash != user.hash):
        # increment login attempts
        try_except(
            lambda: admin_col.update_one({ 
                    "_id": ObjectId(user.id) 
                }, { 
                    "$set": { "login_attempts": user.login_attempts + 1 }
                }),
            "Could not increment login attempts",
            user=user
        )
        raise exception.invalid_credentials

    # reset login attempts
    try_except(
        lambda: admin_col.update_one({ 
                "_id": ObjectId(user.id) 
            }, { 
                "$set": { "login_attempts": 0 }
            }),
        "Could not reset login attempts",
        user=user
    )
    
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

    logger.info(f"Admin {user.id} authenticated.")
    # can't use success.ok() becase cookies will not be included breaking the endpoint.
    return { "message": "User authenticated." }

@admin_router.post("/admin/register", tags=["Admin Account"])
def admin_register(credentials: AdminCredentialsModel):

    user_exist = try_except(
        lambda: admin_col.find_one({ "email": credentials.email }) is not None,
        "A MongoDB error occured.",
        credentials=credentials
    )

    if (user_exist):
        raise exception.data_conflict("Email already used.")
    
    verification_code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    # TODO: Add link to frontend
    message = f"You verification code is {verification_code}"

    try_except(
        lambda: send_verification_email("Warden", credentials.email, message),
        "Failed to send verification code to email.",
        credentials=credentials
    )

    user_id = try_except(
        lambda: admin_col.insert_one({
                "email": credentials.email,
                "hash": hash(credentials.hash),
                "apps": [],
                "login_attempts": 0,
                "verification_code": verification_code
            }).inserted_id,
        "Failed to insert admin user in DB.",
        credentials=credentials
    )

    logger.info(f"Admin {user_id} registered successfully.")
    return success.created("Admin registered successfully.")

@admin_router.get("/admin/logout", tags=["Admin Account"])
def admin_logout(res: Response):
    res.delete_cookie(key="access_token")
    res.delete_cookie(key="refresh_token")

    # can't use success.ok() becase cookies removal will not be included breaking the endpoint.
    return { "message": "User logged out." }

@admin_router.post("/admin/{user_id}/verify", tags=["Admin Account"])
def verify_account(body: UnverifiedAdminCredentialsModel, user_id: str):
    user = try_except(
        lambda: admin_col.find_one({ "_id": ObjectId(user_id) }),
        "A MongoDB error occured.",
        user_id=user_id
    )

    if (not user):
        raise exception.invalid_credentials

    user: AdminUserModel = try_except(
        lambda: UnverifiedAdminUserModel(**user),
        "Invalid admin user data from DB.",
        user=user
    )
    
    if (user.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        raise exception.account_locked
    
    if (body.verification_code != user.verification_code):
        # increment login attempts when wrong password
        try_except(
            lambda: admin_col.update_one({ 
                    "_id": ObjectId(user.id) 
                }, { 
                    "$set": { "login_attempts": user.login_attempts + 1 }
                }),
            "Could not increment login attempts.",
            user=user
        )

    try_except(
        lambda: admin_col.update_one({ 
                "_id": ObjectId(user.id) 
            }, { 
                "$set": { 
                    "login_attempts": 0,
                },
                "$unset": {
                    "verification_code": ""
                }
            }),
        "Could not reset login attempts.",
        user=user
    )

    logger.info(f"Admin {user.id} was verified.")
    return success.ok("Account verified successfully.")

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
    try_except(
        lambda: admin_col.update_one({
                "_id": ObjectId(user.id)
            }, {
                "$set": { "hash": double_new_hash }
            }),
        "Could not set hash.",
        body=body,
        user=user
    )

    logger.info(f"Admin {user.id} successfully changed password.")
    return success.ok("Password changed successfully.")

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
    
    app.api_key_hash = ""

    # create collection for new app
    try_except(
        lambda: db.create_collection(f"app_{user.id}_{app.name}"),
        "Could not create collection.",
        user=user,
        app=app
    )

    # update user apps
    try_except(
        lambda: admin_col.update_one(
                { "_id": ObjectId(user.id) }, 
                { "$push": { "apps": app.model_dump() }}
            ),
        "Could not update user apps.",
        user=user,
        app=app
    )

    logger.info(f"Admin {user.id} registered app {app.name}.")
    return success.created(f"App {app.name} has been registered.")

@admin_router.put("/admin/app/{app_name}", tags=["Admin Apps"])
def admin_update_app(app: AppMetadataModel, app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        raise exception.data_conflict("App doesn't exist.")
    
    if (app.api_key_hash != None):
        raise exception.bad_request("Manual setting of api key is not allowed.")

    # if changing name, rename collection
    if (app.name != app_name):
        if (app_exist(app.name, user.apps)):
            raise exception.data_conflict("App already exists.")
    
        try_except(
            lambda: db[f"app_{user.id}_{app_name}"].rename(f"app_{user.id}_{app.name}"),
            "Could not rename collection.",
            user=user,
            app=app
        )

    try_except(
        lambda: admin_col.update_one(
                { "_id": ObjectId(user.id) }, 
                {"$set": { 
                    "apps.$[elem].name": app.name,
                    "apps.$[elem].access_token_exp_sec": app.access_token_exp_sec,
                    "apps.$[elem].refresh_token_exp_sec": app.refresh_token_exp_sec,
                    "apps.$[elem].max_login_attempts": app.max_login_attempts,
                    "apps.$[elem].lockout_time_per_attempt_sec": app.lockout_time_per_attempt_sec
                }}, 
                array_filters=[{"elem.name": app_name}]
            ),
        "Could not update user apps.",
        user=user,
        app=app
    )

    logger.info(f"Admin {user.id} updated app {app.name}.")
    return success.ok(f"App {app_name} has been updated.")

@admin_router.get("/admin/app/{app_name}/generate_api_key", tags=["Admin Apps"], response_model=str)
def admin_generate_api_key(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        raise exception.data_conflict("App doesn't exist.")

    api_key = generate_api_key()
    api_key_hash = hash(api_key)

    try_except(
        lambda: admin_col.update_one(
                { "_id": ObjectId(user.id) }, 
                {"$set": { 
                    "apps.$[elem].api_key_hash": api_key_hash,
                }}, 
                array_filters=[{"elem.name": app_name}]
            ),
        "Could not set user hash.",
        app_name=app_name,
        user=user
    )

    logger.info(f"Admin {user.id} generated API key for app {app_name}.")
    return api_key

@admin_router.delete("/admin/app/{app_name}", tags=["Admin Apps"])
def admin_delete_app(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (not app_exist(app_name, user.apps)):
        raise exception.data_conflict(f"App {app_name} doesn't exist.")

    try_except(
        lambda: db[f"app_{user.id}_{app_name}"].drop(),
        "Could not drop collection.",
        app_name=app_name,
        user=user
    )

    try_except(
        lambda: admin_col.update_one(
            { "_id": ObjectId(user.id) }, 
            {"$pull": { "apps": { "name": app_name }}}, 
        ),
        "Could not remove app from user apps.",
        app_name=app_name,
        user=user
    )

    logger.info(f"Admin {user.id} deleted app {app_name}.")
    return success.ok(f"App {app_name} deleted.")
