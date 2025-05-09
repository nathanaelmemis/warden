from pydantic import BaseModel

class AdminCredentialsModel(BaseModel):
    email: str
    hash: str