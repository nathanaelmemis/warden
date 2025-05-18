from typing import Annotated
from pydantic import BaseModel, BeforeValidator, Field

from models.AppMetadataModel import AppMetadataModel

class AdminUserModel(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(alias='_id')
    email: str
    hash: str
    apps: list[AppMetadataModel]
    login_attempts: int