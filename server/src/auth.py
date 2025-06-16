from datetime import datetime
import uuid
from bson import ObjectId
from fastapi import Depends, Request
from jose import jwt
import os
import hashlib
from pymongo.collection import Collection

from models import Admin, App, User
from utils import exception
from database import db

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["HASHING_ALGORITHM"]

admin_col = db.admin
app_col = db.app


def generate_token(data: dict, expire: datetime):
    to_encode = data.copy()
    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt

def hash(text: str):
    return hashlib.sha256(text.encode()).hexdigest()

def generate_api_key():
    return hash(str(uuid.uuid4()))

def get_current_admin(req: Request):
    access_token = req.cookies.get("access_token")

    if (not access_token):
        raise exception.unauthorized_access

    try:
        admin_id = jwt.decode(access_token, SECRET_KEY, ALGORITHM)["id"]

        admin: dict = admin_col.find_one({ "_id": ObjectId(admin_id) })

        if (not admin):
            raise exception.unauthorized_access

        if (admin.get("verification_code")):
            return exception.account_not_verified

        return Admin(**admin)
    except:
        raise exception.invalid_access_token
    
def get_app(req: Request):
    app_id = req.headers.get("Warden-App-API-ID")
    app_api_token = req.headers.get("Warden-App-API-Key")

    if (app_id == None or app_api_token == None):
        raise exception.missing_headers
    
    api_key_hash = hash(app_api_token)

    app = app_col.find_one({ 
        "_id": ObjectId(app_id), 
        "api_key_hash": api_key_hash
    })

    if (not app):
        raise exception.invalid_headers

    return App(**app)

def get_app_and_current_user(req: Request, app: App = Depends(get_app)):
    app_col = db[f"app_{app.id}"]

    access_token = req.cookies.get("access_token")

    if (not access_token):
        raise exception.unauthorized_access

    try:
        user_id = jwt.decode(access_token, SECRET_KEY, ALGORITHM)["id"]

        user: dict = app_col.find_one({ "_id": ObjectId(user_id) })

        if (not user):
            raise exception.unauthorized_access

        if (user.get("verification_code")):
            return exception.account_not_verified

        return app, User(**user)
    except:
        raise exception.invalid_access_token