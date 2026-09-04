import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5500"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def owner_and_widget(client):
    import uuid
    email = f"owner-{uuid.uuid4().hex[:8]}@test.com"
    signup = client.post("/auth/signup", json={
        "tenant_name": "Test Co", "email": email, "password": "supersecret123",
    })
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    widget_resp = client.post("/widgets", headers=headers, json={
        "type": "signup_form",
        "title": "Test Widget",
        "fields": [{"name": "email", "label": "Email", "field_type": "email", "required": True}],
    })
    widget_id = widget_resp.json()["id"]
    return {"headers": headers, "widget_id": widget_id}
