import pytest
from main import app, db
from datetime import datetime
import pytz

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_log_event_success(client):
    payload = {
        "account_id": "test_acct",
        "endpoint": "/api/test",
        "timestamp": datetime.now(pytz.UTC).isoformat()
    }
    response = client.post("/log-event", json=payload)
    assert response.status_code == 201
    assert response.json["message"] == "Event logged"


def test_log_event_missing_account_id(client):
    payload = {
        "endpoint": "/api/test",
        "timestamp": datetime.now(pytz.UTC).isoformat()
    }
    response = client.post("/log-event", json=payload)
    assert response.status_code == 400
    assert "Missing required fields" in response.get_data(as_text=True)

def test_log_event_missing_endpoint(client):
    payload = {
        "account_id": "test_acct",
        "timestamp": datetime.now(pytz.UTC).isoformat()
    }
    response = client.post("/log-event", json=payload)
    assert response.status_code == 400
    assert "Missing required fields" in response.get_data(as_text=True)

def test_log_event_missing_timestamp(client):
    payload = {
        "account_id": "test_acct",
        "endpoint": "/api/test"
    }
    response = client.post("/log-event", json=payload)
    assert response.status_code == 400
    assert "Missing required fields" in response.get_data(as_text=True)

def test_log_event_invalid_timestamp_format(client):
    payload = {
        "account_id": "test_acct",
        "endpoint": "/api/test",
        "timestamp": "not-a-date"
    }
    response = client.post("/log-event", json=payload)
    assert response.status_code == 500 or response.status_code == 400
    assert "error" in response.json
