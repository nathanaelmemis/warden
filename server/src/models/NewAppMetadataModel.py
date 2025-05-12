from pydantic import BaseModel


class NewAppMetadataModel(BaseModel):
    access_token_exp_sec: int
    refresh_token_exp_sec: int
    max_login_attempts: int
    lockout_time_per_attempt_sec: int