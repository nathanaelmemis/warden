from pydantic import BaseModel

from models import AppID, AppAPIKey, AppBase


class AppCreate(AppBase):
    pass

class AppUpdate(AppBase):
    pass

class AppInsert(AppBase, AppAPIKey):
    pass

class AppResponse(AppID, AppBase):
    pass

class AppApiKeyResponse(AppID, AppAPIKey):
    pass


class Credentials(BaseModel):
    email: str
    hash: str

class ChangePassword(Credentials):
    new_hash: str


class VerificationCode(BaseModel):
    verification_code: str

class UserData(BaseModel):
    pass