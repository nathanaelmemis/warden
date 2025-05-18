from pydantic import BaseModel


class UnverifiedAdminCredentialsModel(BaseModel):
    verification_code: str