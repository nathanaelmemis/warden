
from pydantic import BaseModel


class AppMetadataModel(BaseModel):
    name: str
    access_token_exp_sec: int
    refresh_token_exp_sec: int
    max_login_attempts: int
    lockout_time_per_attempt_sec: int
    api_key_hash: str