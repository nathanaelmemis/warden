from typing import Annotated
from pydantic import BaseModel, BeforeValidator, Field


class UnverifiedAdminUserModel(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(alias='_id')
    email: str
    hash: str
    apps: dict
    login_attempts: int
    account_verified: False