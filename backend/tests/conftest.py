import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas-0123456789abcdef"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth(client):
    r = client.post(
        "/api/users",
        json={"user": {"username": "omar", "email": "omar@example.com", "password": "clave-segura-1"}},
    )
    return {"Authorization": f"Token {r.json()['user']['token']}"}
