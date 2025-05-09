from typing import Union
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from admin import admin_router

app = FastAPI()

app.include_router(admin_router)