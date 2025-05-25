from typing import Annotated
from pydantic import BaseModel, BeforeValidator, Field


class AppBase(BaseModel):
    name: str
    access_token_exp_sec: int
    refresh_token_exp_sec: int
    max_login_attempts: int
    lockout_time_per_attempt_sec: int

class ApiId(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(alias='_id')

class AppAPIKey(BaseModel):
    api_key_hash: str

class App(ApiId, AppBase, AppAPIKey):
    pass


class Admin(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(alias='_id')
    email: str
    hash: str
    apps: list[App]
    login_attempts: int

class UnverifiedAdmin(BaseModel):
    verification_code: str