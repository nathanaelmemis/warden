from bson import ObjectId
from dotenv import load_dotenv

from models.Admin import Admin
load_dotenv(dotenv_path=".env.development")

from fastapi.testclient import TestClient
from main import app
from auth import get_current_user
import os
from database import db

admin_col = db.admin

def override_get_current_user():
    return Admin(**admin_col.find_one({ "_id": ObjectId("6821da0dd771d53184de590d") }))

app.dependency_overrides[get_current_user] = override_get_current_user

def test_admin_insert_mock_data():
    admin_col.insert_one({
        "_id": ObjectId("6821da0dd771d53184de590d"),
        "email": "test@gmail.com",
        "hash": "52bb07742f70942d9cd9a9cf1642045953ab344c08bcf9ba5bf35ed6c1990c3c",
        "apps": [],
        "login_attempts": 0,
    })

client = TestClient(app)

def test_environment_variables():
    secret_key = os.environ.get("SECRET_KEY")
    assert secret_key is not None, "API_KEY environment variable not set"
    mongodb_url = os.environ.get("MONGODB_URL")
    assert mongodb_url is not None, "MONGODB_URL environment variable not set"

def test_admin_login():
    res = client.post("/admin/login", json={ "email": "test@gmail.com", "hash": "fdd8157ddd7d2ade12a3799aa9998a8de76d291c1f3ddce3b3bb7edb2f42c7a8" })
    assert res.status_code == 200

def test_admin_register_app():
    res = client.post("/admin/app", json={
        "name": "test_app_a",
        "access_token_exp_sec": 99,
        "refresh_token_exp_sec": 99,
        "max_login_attempts": 99,
        "lockout_time_per_attempt_sec": 99,
    })
    assert res.status_code == 201

def test_admin_update_app():
    res = client.put("/admin/app/test_app_a", json={
        "name": "test_app_b",
        "access_token_exp_sec": 100,
        "refresh_token_exp_sec": 100,
        "max_login_attempts": 100,
        "lockout_time_per_attempt_sec": 100,
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

def test_admin_cleanup():
    admin_col.delete_one({
        "_id": ObjectId("6821da0dd771d53184de590d"),
    })