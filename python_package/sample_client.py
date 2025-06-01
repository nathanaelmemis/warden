import asyncio
import os
from typing import List

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.testclient import TestClient
from pydantic import BaseModel

from warden import FastAPI_Warden

os.environ.setdefault("WARDEN_ENV", "DEV")

warden = FastAPI_Warden(
    "683bfaa26caa16a64f98f5e4", 
    "1d6eae59d4cc2e8950e4066dd1efd7ec4a22a59ff587f4adabbdcf5da338f73f"
)

app = FastAPI()

app_router = APIRouter()

app_router.add_api_route("/login", warden.login, methods=["GET"])

app_router.add_api_route("/user", warden.update_user_data, methods=["PATCH"])


# async def test():
#     response = await warden.register("nathanaelmemis@gmail.com", "nathanaelmemis")
#     print(response)

# async def test():
#     response = await warden.verify_account("683bff46216b979b4950e8ad", "266309")
#     print(response)

# async def test_login():
#     response = await warden.login("nathanaelmemis@gmail.com", "nathanaelmemis")
#     print(response)

# async def test_update_user_data():
#     response = await warden.update_user_data({
#         "name": "Nathan",
#         "age": 23,
#         "sample_dict": {
#             "test_a": "meow",
#             "test_b": 123
#         },
#         "sample_array": [1, 2, 3, 4, 5]
#     })
#     print(response)

# asyncio.run(test_login())
# asyncio.run(test_update_user_data())

app.include_router(app_router)