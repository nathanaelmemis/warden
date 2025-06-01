from bson import ObjectId
from dotenv import load_dotenv

from models import Admin, App, UnverifiedAdmin, UnverifiedUser
from schemas import AppResponse
load_dotenv(dotenv_path=".env.development")

from fastapi.testclient import TestClient
from main import app
from auth import get_current_admin
import os
from database import db

admin_col = db.admin

client = TestClient(app)

def test_environment_variables():
    secret_key = os.environ.get("SECRET_KEY")
    assert secret_key is not None, "API_KEY environment variable not set"
    mongodb_url = os.environ.get("MONGODB_URL")
    assert mongodb_url is not None, "MONGODB_URL environment variable not set"

def test_admin_create_account():
    res = client.post("/admin/register", json={ "email": "test@gmail.com", "hash": "test" })
    assert res.status_code == 201

    admin_id = res.json()["message"]

    admin = UnverifiedAdmin(**admin_col.find_one({ "_id": ObjectId(admin_id) }))

    res = client.post(f"/admin/{admin_id}/verify", json={ "verification_code": admin.verification_code })
    assert res.status_code == 200

def test_admin_login():
    res = client.post("/admin/login", json={ "email": "test@gmail.com", "hash": "test" })
    assert res.status_code == 200

    return res

def test_admin_change_password():
    res = test_admin_login()

    res = client.patch("/admin/changepassword", 
        json={ 
            "email": "test@gmail.com", 
            "hash": "test",
            "new_hash": "testing" 
        }
    )
    assert res.status_code == 200

    res = client.post("/admin/login",
        json={ 
            "email": "test@gmail.com", 
            "hash": "testing" 
        }
    )
    assert res.status_code == 200

    res = client.patch("/admin/changepassword", 
        json={ 
            "email": "test@gmail.com", 
            "hash": "testing",
            "new_hash": "test" 
        }
    )
    assert res.status_code == 200

def test_admin_app():
    res = test_admin_login()

    res = client.post("/admin/app", json={
        "name": "test_app_test",
        "access_token_exp_sec": 99,
        "refresh_token_exp_sec": 99,
        "max_login_attempts": 99,
        "lockout_time_per_attempt_sec": 99
    })
    assert res.status_code == 201

    app_id = res.json()["message"]
    
    res = client.patch(f"/admin/app/{app_id}", json={
        "name": "test_app",
        "access_token_exp_sec": 100,
        "refresh_token_exp_sec": 100,
        "max_login_attempts": 100,
        "lockout_time_per_attempt_sec": 100
    })
    assert res.status_code == 200

    res = client.get(f"/admin/app/{app_id}/generate_api_key")
    assert res.status_code == 200

def test_app():
    res = test_admin_login()

    res = client.get("/admin/app")
    assert res.status_code == 200

    app = AppResponse(**res.json()[0])

    res = client.get(f"/admin/app/{app.id}/generate_api_key")
    assert res.status_code == 200

    app_api_key = res.json()["message"]

    res = client.post(
        url="/user/register", 
        headers={
            "Warden-App-API-ID": app.id,
            "Warden-App-API-Key": app_api_key
        },
        json={ 
            "email": "apptest@gmail.com", 
            "hash": "apptest" 
        }
    )
    assert res.status_code == 201

    user_id = res.json()["message"]

    app_col = db[f"app_{app.id}"]

    user = UnverifiedUser(**app_col.find_one({ "_id": ObjectId(user_id) }))

    res = client.post(
        url=f"/user/{user_id}/verify", 
        headers={
            "Warden-App-ID": app.id,
            "Warden-App-API-Token": app_api_key
        },
        json={ "verification_code": user.verification_code }
    )
    assert res.status_code == 200

    res = client.post(
        url="/user/login",
        headers={
            "Warden-App-ID": app.id,
            "Warden-App-API-Token": app_api_key
        }, 
        json={ "email": "apptest@gmail.com", "hash": "apptest" }
    )
    assert res.status_code == 200

    res = client.get(
        url="/user",
        headers={
            "Warden-App-ID": app.id,
            "Warden-App-API-Token": app_api_key
        }
    )
    assert res.status_code == 200

    res = client.patch(
        url="/user",
        headers={
            "Warden-App-ID": app.id,
            "Warden-App-API-Token": app_api_key
        }, 
        json={ "testDataA": 123, "testDataB": "456" }
    )
    assert res.status_code == 200

    res = client.patch(
        url="/user/changepassword",
        headers={
            "Warden-App-ID": app.id,
            "Warden-App-API-Token": app_api_key
        }, 
        json={ 
            "email": "apptest@gmail.com", 
            "hash": "apptest",
            "new_hash": "apptesting"
        }
    )
    assert res.status_code == 200

    res = client.delete(
        url="/user",
        headers={
            "Warden-App-ID": app.id,
            "Warden-App-API-Token": app_api_key
        }, 
    )
    assert res.status_code == 200


def test_admin_cleanup():
    res = client.post("/admin/login", json={ "email": "test@gmail.com", "hash": "test" })
    assert res.status_code == 200
    
    res = client.get("/admin/app")
    assert res.status_code == 200

    app = AppResponse(**res.json()[0])

    res = client.delete(f"/admin/app/{app.id}")
    assert res.status_code == 200

    res = client.delete("/admin")
    assert res.status_code == 200

    res = client.get("/admin/logout")
    assert res.status_code == 200