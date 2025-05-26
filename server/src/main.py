import json
from typing import Callable
from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv
import os

from fastapi.responses import JSONResponse
from fastapi import status

from utils import exception
from utils.logging import logger

load_dotenv()

ENV_VARIABLES = ["SECRET_KEY", "MONGODB_URL", "EMAIL_SERVICE_USER", "EMAIL_SERVICE_PASSWORD"]

for env_var in ENV_VARIABLES:
    if (os.environ.get(env_var) is None):
        raise EnvironmentError(f"{env_var} environment variable is not set.")

from routers.admin import admin_router
from routers.app import app_router

app = FastAPI()

@app.middleware("http")
async def error_logger(request: Request, call_next):
    req_body = await request.body()

    if (req_body.__len__() > 0):
        req_body = json.loads(req_body)

    try:
        response = await call_next(request)
    except HTTPException:
        return response
    except Exception as error:
        logger.error(
            f"{request.method} {request.url}\n{type(error).__name__}", 
            error, 
            query_params = request.query_params, 
            body = req_body
        )
        return JSONResponse(
            { "reason": type(error).__name__ }, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return response

app.include_router(admin_router)
app.include_router(app_router)