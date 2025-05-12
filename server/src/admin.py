from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import uuid
from models.NewAppMetadataModel import NewAppMetadataModel
from models.AppMetadataModel import AppMetadataModel
from models.UpdateAppMetadataMode import UpdateAppMetadataModel
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

@protected_admin_router.post("/admin/app/{app_name}")
def register_app(app_name: str, body: NewAppMetadataModel, user: AdminUserModel = Depends(get_current_user)):
    if (app_name in user.apps):
        return exception.data_conflict("App already exists.")
    
    new_app = body.model_dump(exclude=["name"])
    new_app.update({ "api_key_hash": "" })
    
    updated_apps: dict = user.model_dump()["apps"]
    updated_apps.update({ app_name: new_app })
    
    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "message": f"{app_name} has been registered."}

@protected_admin_router.put("/admin/app/{app_name}")
def update_app(body: UpdateAppMetadataModel, app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (app_name not in user.apps):
        return exception.data_conflict("App doesn't exist.")
    
    updated_apps: dict = user.model_dump()["apps"]
    del updated_apps[app_name]
    
    updated_app = body.model_dump(exclude=["name"])
    updated_app.update({ "api_key_hash": "" })
    
    updated_apps.update({ body.name: updated_app })
    
    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "message": f"{app_name} has been updated."}

@protected_admin_router.get("/admin/app/{app_name}/generate_api_key")
def generate_api_key(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (app_name not in user.apps):
        return exception.data_conflict("App doesn't exist.")
    
    api_key = hash(str(uuid.uuid4()))

    updated_apps: dict = user.model_dump()["apps"]
    updated_apps[app_name]["api_key_hash"] = hash(api_key)

    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "api_key": api_key }

@protected_admin_router.delete("/admin/app/{app_name}")
def delete_app(app_name: str, user: AdminUserModel = Depends(get_current_user)):
    if (app_name not in user.apps):
        return exception.data_conflict("App doesn't exist.")

    updated_apps: dict = user.model_dump()["apps"]
    del updated_apps[app_name]

    admin_col.update_one({ "_id": ObjectId(user.id) }, { "$set": { "apps": updated_apps }})

    return { "message": f"{app_name} deleted successfully." }


admin_router.include_router(protected_admin_router)