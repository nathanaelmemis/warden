from typing import Annotated
from pydantic import BaseModel, BeforeValidator, Field


AnnotatedObjectId = Annotated[str, BeforeValidator(str)]


class AppBase(BaseModel):
    name: str
    access_token_exp_sec: int
    refresh_token_exp_sec: int
    max_login_attempts: int
    lockout_time_per_attempt_sec: int

class AppID(BaseModel):
    id: AnnotatedObjectId = Field(alias='_id')

class AppAPIKey(BaseModel):
    api_key_hash: str

class App(AppID, AppBase, AppAPIKey):
    pass


class Admin(BaseModel):
    id: AnnotatedObjectId = Field(alias='_id')
    email: str
    hash: str
    apps: list[AnnotatedObjectId]
    login_attempts: int

class UnverifiedAdmin(Admin):
    verification_code: str


class User(BaseModel):
    id: AnnotatedObjectId = Field(alias='_id')
    email: str
    hash: str
    login_attempts: int
    data: dict

class UnverifiedUser(User):
    verification_code: str