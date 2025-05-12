from dotenv import load_dotenv

from schemas.AdminUserModel import AdminUserModel
load_dotenv(dotenv_path=".env.development")

from fastapi.testclient import TestClient
from main import app
from utils.auth import get_current_user
import os

def override_get_current_user():
    return AdminUserModel(
        _id="6821da0dd771d53184de590d",
        email="nathanaelmemis@email.com",
        hash="test_hash",
        apps={
            "test_app_a": {
                "access_token_exp_sec": 99,
                "refresh_token_exp_sec": 99,
                "max_login_attempts": 99,
                "lockout_time_per_attempt_sec": 99,
                "api_key_hash": "test_api_key_hash"
            }
        },
        login_attempts=0
    )

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_environment_variables():
    secret_key = os.environ.get("SECRET_KEY")
    assert secret_key is not None, "API_KEY environment variable not set"
    mongodb_url = os.environ.get("MONGODB_URL")
    assert mongodb_url is not None, "MONGODB_URL environment variable not set"

def test_admin_login():
    res = client.post("/admin/login", json={ "email": "nathanaelmemis@gmail.com", "hash": "nathanaelmemis" })
    assert res.status_code == 200

def test_admin_register_app():
    res = client.post("/admin/app/test_app_b", json={
        "access_token_exp_sec": 99,
        "refresh_token_exp_sec": 99,
        "max_login_attempts": 99,
        "lockout_time_per_attempt_sec": 99
    })
    assert res.status_code == 200

def test_admin_update_app():
    res = client.put("/admin/app/test_app_b", json={
        "access_token_exp_sec": 100,
        "refresh_token_exp_sec": 100,
        "max_login_attempts": 100,
        "lockout_time_per_attempt_sec": 100,
        "name": "test_app_b"
    })
    assert res.status_code == 200

def test_admin_generate_api_key():
    res = client.get("/admin/app/test_app_b/generate_api_key")
    assert res.status_code == 200

def test_admin_delete_app():
    res = client.delete("/admin/app/test_app_b")
    assert res.status_code == 200


def test_admin_logout():
    res = client.get("/admin/logout")
    assert res.status_code == 200