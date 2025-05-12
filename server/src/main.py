from typing import Union
from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

secret_key = os.environ.get("SECRET_KEY")
if (secret_key is None):
    raise EnvironmentError("SECRET_KEY environment variable is not set.")
mongodb_url = os.environ.get("MONGODB_URL")
if (mongodb_url is None):
    raise EnvironmentError("MONGODB_URL environment variable is not set.")

from admin import admin_router

app = FastAPI()

app.include_router(admin_router)