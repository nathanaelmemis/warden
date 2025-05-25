from pydantic import BaseModel

from models import ApiId, AppAPIKey, AppBase


class AppCreate(AppBase):
    pass

class AppUpdate(AppBase):
    pass

class AppApiKeyResponse(ApiId, AppAPIKey):
    pass


class Credentials(BaseModel):
    email: str
    hash: str

class ChangePassword(Credentials):
    new_hash: str