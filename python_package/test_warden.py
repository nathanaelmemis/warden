import asyncio
import os

from Warden import Warden

os.environ.setdefault("WARDEN_ENV", "DEV")

warden = Warden("test_api_id", "test_api_key")

class Data:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

async def test_login():
    response = await warden.get_user_data(Data)
    response
    print(response.model_dump())
    print(response.email)

asyncio.run(test_login())