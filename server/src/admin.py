from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from models.NewAppModel import NewAppModel
from utils.database import db

from models.AdminCredentialsModel import AdminCredentialsModel
import utils.exception as exception
from schemas.AdminUserModel import AdminUserModel
from utils.auth import generate_token, get_current_user, hash
import utils.success as success

ADMIN_ALLOWED_LOGIN_ATTEMPTS = 3
ADMIN_ACCESS_TOKEN_EXP_MINS = 10
ADMIN_REFRESH_TOKEN_EXP_MINS = 60

admin_col = db.admin


admin_router = APIRouter()

@admin_router.post("/admin/login")
def admin_login(body: AdminCredentialsModel, res: Response):
    admin_user = AdminUserModel(**admin_col.find_one({ "email": body.email}))

    if (not admin_user):
        return exception.invalid_credentials
    
    if (admin_user.login_attempts >= ADMIN_ALLOWED_LOGIN_ATTEMPTS):
        return exception.account_locked
    
    double_hash = hash(body.hash)
    if (double_hash != admin_user.hash):
        # increment login attempts when wrong password
        admin_col.update_one({ 
                "_id": ObjectId(admin_user.id) 
            }, { 
                "$set": { "login_attempts": admin_user.login_attempts + 1 }
            })
        return exception.invalid_credentials
    
    # reset login attempts when authenticated
    admin_col.update_one({ 
            "_id": ObjectId(admin_user.id) 
        }, { 
            "$set": { "login_attempts": 0 }
        })
    
    access_token_exp = datetime.utcnow() + timedelta(minutes=ADMIN_ACCESS_TOKEN_EXP_MINS)
    refresh_token_exp = datetime.utcnow() + timedelta(minutes=ADMIN_ACCESS_TOKEN_EXP_MINS)

    access_token_data = admin_user.model_dump(exclude={"hash"})
    refresh_token_data = { "_id": admin_user.id }
    
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

@admin_router.get("/admin/logout")
def admin_logout(res: Response):
    res.delete_cookie(key="access_token")
    res.delete_cookie(key="refresh_token")

    return { "message": "User logged out" }


protected_admin_router = APIRouter()

@protected_admin_router.post("/admin/register_app")
def register_app(body: NewAppModel, user: AdminUserModel = Depends(get_current_user)):
    user_apps = admin_col.find({ "_id": ObjectId(user.id) }, { "apps": True })

    print(user_apps)

    if (body.name in user_apps):
        return "ngew"


admin_router.include_router(protected_admin_router)