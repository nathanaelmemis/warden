from typing import Callable
from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv
import os

from utils import exception
from utils.logging import logger

load_dotenv()

ENV_VARIABLES = ["SECRET_KEY", "MONGODB_URL", "EMAIL_SERVICE_USER", "EMAIL_SERVICE_PASSWORD"]

for env_var in ENV_VARIABLES:
    if (os.environ.get(env_var) is None):
        raise EnvironmentError(f"{env_var} environment variable is not set.")

from routers.admin import admin_router

app = FastAPI()

# @app.middleware("http")
# async def error_logger(request: Request, call_next):
#     try:
#         response = await call_next(request)
#     except HTTPException:
#         return response
#     except Exception as error:
#         logger.error(request.base_url, error, query_params=request.query_params, body=request.body())
#         raise exception.internal_server_error

app.include_router(admin_router)
