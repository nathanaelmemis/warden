from datetime import datetime, timedelta
import secrets
from bson import ObjectId
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from models import App, UnverifiedUser, User
from schemas import ChangePassword, Credentials, UserData, VerificationCode

from database import db
from utils import success
from utils.email import send_verification_email
from utils.logging import logger
import utils.exception as exception
from auth import generate_token, get_app, get_app_and_current_user, hash


app_router = APIRouter()

# Unprotected routes

@app_router.post("/user/login", tags=["User Account"])
def user_login(credentials: Credentials, res: Response, app: App = Depends(get_app)):
    app_col = db[f"app_{app.id}"]

    user: dict = app_col.find_one({ "email": credentials.email })

    if (not user):
        raise exception.invalid_credentials

    if (user.get("verification_code")):
        raise exception.account_not_verified
    
    user: User = User(**user)

    if (user.login_attempts >= app.max_login_attempts):
        raise exception.account_locked

    double_hash = hash(credentials.hash)

    if (double_hash != user.hash):
        # increment login attempts
        app_col.update_one({ 
            "_id": ObjectId(user.id) 
        }, { 
            "$set": { "login_attempts": user.login_attempts + 1 }
        })
        raise exception.invalid_credentials

    # reset login attempts
    app_col.update_one({ 
        "_id": ObjectId(user.id) 
    }, { 
        "$set": { "login_attempts": 0 }
    })
    
    access_token_exp = datetime.utcnow() + timedelta(seconds=app.access_token_exp_sec)
    refresh_token_exp = datetime.utcnow() + timedelta(seconds=app.refresh_token_exp_sec)

    access_token_data = user.model_dump(exclude={"hash"})
    refresh_token_data = { "_id": user.id }
    
    access_token = generate_token(access_token_data, access_token_exp)
    refresh_token = generate_token(refresh_token_data, refresh_token_exp)
    
    res.set_cookie(
        "access_token", 
        access_token,
        httponly=True,
        samesite="strict",
        max_age=app.access_token_exp_sec,
    )
    res.set_cookie(
        "refresh_token", 
        refresh_token,
        httponly=True,
        samesite="strict",
        max_age=app.refresh_token_exp_sec,
    )

    logger.info(f"App {app.id} - User {user.id} authenticated.")
    # can't use success.ok() becase cookies will not be included breaking the endpoint.
    return { "message": "User authenticated." }

@app_router.post("/user/register", tags=["User Account"])
def user_register(credentials: Credentials, app: App = Depends(get_app)):
    app_col = db[f"app_{app.id}"]

    user_exist = app_col.find_one({ "email": credentials.email }) is not None

    if (user_exist):
        raise exception.data_conflict("Email already used.")
    
    verification_code = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    # TODO: Add link to frontend
    message = f"You verification code is {verification_code}"

    send_verification_email(app.name, credentials.email, message)

    user_id = app_col.insert_one({
            "email": credentials.email,
            "hash": hash(credentials.hash),
            "data": {},
            "login_attempts": 0,
            "verification_code": verification_code
        }).inserted_id

    logger.info(f"App {app.id} - User {str(user_id)} registered successfully.")
    return success.created(str(user_id))

@app_router.post("/user/{user_id}/verify", tags=["Admin Account"])
def user_verify_account(body: VerificationCode, user_id: str, app: App = Depends(get_app)):
    app_col = db[f"app_{app.id}"]

    user = app_col.find_one({ "_id": ObjectId(user_id) })

    if (not user):
        raise exception.invalid_credentials

    user = UnverifiedUser(**user)
    
    if (user.login_attempts >= app.max_login_attempts):
        raise exception.account_locked
    
    if (body.verification_code != user.verification_code):
        # increment login attempts when wrong password
        app_col.update_one({ 
                "_id": ObjectId(user.id) 
            }, { 
                "$set": { "login_attempts": user.login_attempts + 1 }
            })

    app_col.update_one({ 
            "_id": ObjectId(user.id) 
        }, { 
            "$set": { 
                "login_attempts": 0,
            },
            "$unset": {
                "verification_code": ""
            }
        })

    logger.info(f"App {app.id} - User {user.id} was verified.")
    return success.ok("Account verified successfully.")

# Protected routes

@app_router.patch("/user/changepassword", tags=["Admin Account"])
def user_change_password(body: ChangePassword, app_user: tuple[App, User] = Depends(get_app_and_current_user)):
    app, user = app_user

    app_col = db[f"app_{app.id}"]

    double_hash = hash(body.hash)
    if (double_hash != user.hash):
        raise exception.invalid_credentials
    
    double_new_hash = hash(body.new_hash)
    app_col.update_one({
            "_id": ObjectId(user.id)
        }, {
            "$set": { "hash": double_new_hash }
        })

    logger.info(f"App {app.id} - User {user.id} successfully changed password.")
    return success.ok("Password changed successfully.")

@app_router.get("/user", tags=["User Account"], response_model=User, response_model_exclude=["_id", "hash", "login_attempts"])
def get_user(app_user: tuple[App, User] = Depends(get_app_and_current_user)):
    app, user = app_user
    
    app_col = db[f"app_{app.id}"]

    app_col.find_one({ "_id": user.id })

    logger.info(f"App {app.id} - User {user.id} data updated.")
    return success.ok("User data updated.")

@app_router.patch("/user", tags=["User Account"])
def edit_user(data: UserData, app_user: tuple[App, User] = Depends(get_app_and_current_user)):
    app, user = app_user

    app_col = db[f"app_{app.id}"]

    app_col.update_one({ "_id": user.id }, { "$set": { "data": data.model_dump() }})

    logger.info(f"App {app.id} - User {user.id} data updated.")
    return success.ok("User data updated.")

@app_router.delete("/user", tags=["User Account"])
def delete_user(app_user: tuple[App, User] = Depends(get_app_and_current_user)):
    app, user = app_user

    app_col = db[f"app_{app.id}"]

    app_col.delete_one({ "_id": user.id })

    logger.info(f"App {app.id} - User {user.id} deleted.")
    return success.ok("Account deleted successfully.")