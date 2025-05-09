from fastapi import APIRouter

from database import db

admin_db = db.admin

admin_router = APIRouter()

@admin_router.get("/")
def read_root():
    return {"Hello": "World"}