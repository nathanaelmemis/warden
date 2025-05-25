from datetime import datetime, timedelta
from typing import Callable
import uuid
from bson import ObjectId
from fastapi import Request
from jose import jwt
import os
import hashlib

from models import Admin
from utils import exception
from database import db

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

admin_col = db.admin


def generate_token(data: dict, expire: datetime):
    to_encode = data.copy()
    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt

def hash(text: str):
    return hashlib.sha256(text.encode()).hexdigest()

def generate_api_key():
    return hash(str(uuid.uuid4()))

def get_current_user(req: Request):
    access_token = req.cookies.get("access_token")

    if (not access_token):
        raise exception.unauthorized_access

    try:
        user_id = jwt.decode(access_token, SECRET_KEY, ALGORITHM)["id"]

        user: dict = admin_col.find_one({ "_id": ObjectId(user_id) })

        if (not user):
            raise exception.unauthorized_access

        if (user.get("verification_code")):
            return exception.account_not_verified

        return Admin(**user)
    except:
        raise exception.invalid_access_token