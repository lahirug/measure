import pytest
from datetime import datetime
import pytz
from measure import create_app, db

app = create_app()

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()

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
    assert "Missing required fields"
