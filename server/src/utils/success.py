from fastapi.responses import JSONResponse
from fastapi import status

def ok(message: str):
    return JSONResponse({ "message": message }, status.HTTP_200_OK)

def created(message: str):
    return JSONResponse({ "message": message }, status.HTTP_201_CREATED)