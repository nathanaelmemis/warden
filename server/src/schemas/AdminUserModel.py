from typing import Annotated
from pydantic import BaseModel, BeforeValidator, Field


class AdminUserModel(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(alias='_id')
    email: str
    hash: str
    apps: list[str]
    login_attempts: int