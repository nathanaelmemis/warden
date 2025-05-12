from datetime import datetime, timedelta
from typing import Callable
from fastapi import Request
from jose import jwt
import os
import hashlib

from schemas.AdminUserModel import AdminUserModel
from utils import exception

PRIVATE_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

def generate_token(data: dict, expire: datetime):
    to_encode = data.copy()
    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, ALGORITHM)
    return encoded_jwt

def hash(text: str):
    return hashlib.sha256(text.encode()).hexdigest()

def get_current_user(req: Request):
    access_token = req.cookies.get("access_token")

    if (not access_token):
        raise exception.unauthorized_access

    try:
        user = jwt.decode(access_token, PRIVATE_KEY, ALGORITHM)
        del user["exp"]
        return AdminUserModel(**user)
    except:
        raise exception.invalid_access_token