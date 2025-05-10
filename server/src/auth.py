from datetime import datetime, timedelta
from jose import jwt
import os
import hashlib

from schemas.AdminUserModel import AdminUserModel

ALGORITHM="HS256"

def generate_token(data: dict, expire: datetime):
    to_encode = data.copy()
    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, os.environ["SECRET_KEY"], algorithm=ALGORITHM)
    return encoded_jwt

def hash(text: str):
    return hashlib.sha256(text.encode()).hexdigest()
