from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from database import db

from models.AdminCredentialsModel import AdminCredentialsModel
import exception
from schemas.AdminUserModel import AdminUserModel
from auth import generate_access_token

admin_col = db.admin

admin_router = APIRouter()

@admin_router.post("/login")
def login(body: AdminCredentialsModel):
    admin_user = AdminUserModel(**admin_col.find_one({ "email": body.email}))

    if (not admin_user):
        return exception.invalid_credentials
    
    if (admin_user.login_attempts >= 3):
        return exception.account_locked
    
    if (not body.hash == admin_user.hash):
        admin_col.update_one({ 
                "_id": ObjectId(admin_user.id) 
            }, { 
                "$set": { "login_attempts": admin_user.login_attempts + 1 }
            })
        return exception.invalid_credentials
    
    return generate_access_token(admin_user)