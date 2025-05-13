from typing import Union
from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

ENV_VARIABLES = ["SECRET_KEY", "MONGODB_URL", "EMAIL_SERVICE_USER", "EMAIL_SERVICE_PASSWORD"]

for env_var in ENV_VARIABLES:
    if (os.environ.get(env_var) is None):
        raise EnvironmentError(f"{env_var} environment variable is not set.")

from admin import admin_router

app = FastAPI()

app.include_router(admin_router)