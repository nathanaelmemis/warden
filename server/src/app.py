from fastapi import APIRouter


app_router = APIRouter()

@app_router.get("/app/{app_name}", tags=["Admin Account"])
def get_app():
    pass