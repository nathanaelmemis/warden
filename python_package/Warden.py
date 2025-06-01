from abc import ABC, abstractmethod
import hashlib
import json
import os
from typing import Generic, TypeVar
import fastapi
import httpx
from dotenv import load_dotenv

class Methods:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class _WardenInterface(ABC):
    """
    Interface of Warden.
    """

    def __init__(self, api_id: str, api_key: str):
        self.__api_id = api_id
        self.__api_key = api_key

        load_dotenv()

        if (os.getenv("WARDEN_ENV") == "DEV"):
            self.__warden_server_address = "http://localhost:8000"
        else:
            self.__warden_server_address = "https://warden-nsem.vercel.app"

    def _hash(_, text: str):
        return hashlib.sha256(text.encode()).hexdigest()
    
    async def _query(self, method: Methods, route: str, cookies = None, params = None, body = None):
        headers = {
            "Warden-App-API-ID": self.__api_id,
            "Warden-App-API-Key": self.__api_key
        }
        async with httpx.AsyncClient() as client:
            return await client.request(
                method=method, 
                url=f"{self.__warden_server_address}{route}", 
                headers=headers,
                cookies=cookies,
                params=params, 
                json=body
            )
        
    @abstractmethod
    def _parse_response(self, httpx_res: httpx.Response):
        pass

    @abstractmethod
    async def login():
        pass

    @abstractmethod
    async def register(email: str, password: str):
        pass

    @abstractmethod
    async def verify_account(user_id: str, verification_code: str):
        pass

    @abstractmethod
    async def change_password(email: str, password: str, new_password: str):
        pass

    @abstractmethod
    async def get_user_data():
        pass

    @abstractmethod
    async def update_user_data(user_data: dict):
        pass

    @abstractmethod
    async def delete_user():
        pass

class FastAPI_Warden(_WardenInterface):
    def _parse_response(self, httpx_res: httpx.Response):
        response = fastapi.Response(
            content=httpx_res.content,
            status_code=httpx_res.status_code,
            media_type=httpx_res.headers.get("content-type")
        )

        for cookie in httpx_res.headers.get_list("set-cookie"):
            response.headers.append("set-cookie", cookie)

        return response

    async def login(self, email: str, password: str):
        """
        Login function that performs hashing client-side.
        """

        hash = self._hash(password)
        response = await self._query(
            Methods.POST, 
            "/user/login", 
            body={ 
                "email": email, 
                "hash": hash 
            }
        )
        return self._parse_response(response)

    async def register(self, email: str, password: str):
        """
        Register function that performs hashing client-side.
        """

        hash = self._hash(password)
        response = await self._query(
            Methods.POST, 
            "/user/register", 
            body={ 
                "email": email, 
                "hash": hash 
            }
        )
        return self._parse_response(response)

    async def verify_account(self, user_id: str, verification_code: str):
        response = await self._query(
            Methods.POST, 
            f"/user/{user_id}/verify", 
            body={ 
                "verification_code": verification_code
            }
        )
        return self._parse_response(response)
    
    async def change_password(self, req: fastapi.Request, email: str, password: str, new_password: str):
        password_hash = self._hash(password)
        new_password_hash = self._hash(new_password)
        response = await self._query(
            Methods.PATCH, 
            "/user/changepassword",
            cookies=req.cookies,
            body={ 
                "email": email, 
                "password_hash": password_hash, 
                "new_password_hash": new_password_hash 
            }
        )
        return self._parse_response(response)

    async def get_user_data(self, req: fastapi.Request):
        """
        Get user body.

        Returns:
            dict: Contains email and user body.
        """
        
        response = await self._query(
            Methods.GET, 
            "/user",
            cookies=req.cookies,
        )
        return self._parse_response(response)

    async def update_user_data(self, req: fastapi.Request, user_data: dict):
        response = await self._query(
            Methods.PATCH, 
            "/user",
            cookies=req.cookies,
            body=user_data
        )
        return self._parse_response(response)

    async def delete_user(self, req: fastapi.Request):
        response = await self._query(
            Methods.DELETE, 
            "/user",
            cookies=req.cookies,
        )
        return self._parse_response(response)