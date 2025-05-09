from datetime import datetime, timedelta
from jose import jwt
import os

from schemas.AdminUserModel import AdminUserModel

ALGORITHM="HS256"

def generate_access_token(data: AdminUserModel, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.model_dump()

    expire = datetime.utcnow() + expires_delta
    to_encode.update({ "exp": expire })

    encoded_jwt = jwt.encode(to_encode, os.environ["SECRET_KEY"], algorithm=ALGORITHM)
    return encoded_jwt