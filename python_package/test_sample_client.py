import os
from fastapi.testclient import TestClient

from sample_client import app

os.environ.setdefault("WARDEN_ENV", "DEV")

client = TestClient(app)

def test_env():
    response = client.get("/env")
    assert response.status_code == 200

def test_login():
    response = client.get("/login")
    assert response.status_code == 200

def test_user():
    response = client.get("/user")
    assert response.status_code == 200