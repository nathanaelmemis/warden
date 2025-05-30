import hashlib
import os
from typing import Coroutine, Generic, Optional, TypeVar

T = TypeVar('T') 

class User(Generic[T]):
    def __init__(self, email, data):
        self.email = email
        self.data = data

    def model_dump(self):
        return {
            "email": self.email,
            "data": self.data.__dict__
        }

class Warden:
    def __init__(self, api_id: str, api_key: str):
        self.__api_id = api_id
        self.__api_key = api_key

        if (os.getenv("WARDEN_ENV") == "DEV"):
            self.__warden_server_address = "http://localhost:8000"
        else:
            self.__warden_server_address = "https://warden-nsem.vercel.app"

    def __hash(text: str):
        return hashlib.sha256(text.encode()).hexdigest()
    
    def __query(self, route: str, params: dict = None, body: dict = None):
        # set api credential headers
        pass
            
    async def login(self, email: str, password: str):
        """
        Login function that performs hashing client-side.
        """

        hash = self.__hash(password)

        response = await self.__query("/user/login", body={ email, hash })
        return response

    async def register(self, email: str, password: str):
        """
        Register function that performs hashing client-side.
        """

        hash = self.__hash(password)

        response = await self.__query("/user/register", body={ email, hash })
        return response

    async def verify_account(self, user_id: str, verification_code: str):
        response = await self.__query(f"/user/{user_id}/verify", params={ verification_code })
        return response
    
    async def change_password(self, email: str, password: str, new_password: str):
        password_hash = self.__hash(password)
        new_password_hash = self.__hash(new_password)

        response = await self.__query(f"/user/changepassword", body={ email, password_hash, new_password_hash })
        return response

    async def get_user_data(self, user_model: type[T]) -> User[T]:
        """
        Get user data. Pass a user model for user data serialization.
        """
        
        # response = await self.__query(f"/user")

        # return User[T](**response.data)
        return User[T](email="testEmail", data=user_model(**{"name": "testName", "age": 23}))

    def update_user_data():
        pass

    def delete_user():
        pass