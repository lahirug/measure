import pytest
from measure import create_app, db

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
        "timestamp": "2025-04-09T12:34:56.789123+00:00"
    }
    response = client.post("/log-event", json=payload)
    assert response.status_code == 201
    assert response.json["message"] == "Event logged"

def test_usage_missing_start(client):
    response = client.get("/usage?end=2025-04-10T00:00:00Z")
    assert response.status_code == 400
    assert "Missing required fields" in response.get_data(as_text=True)

def test_usage_missing_end(client):
    response = client.get("/usage?start=2025-04-10T00:00:00Z")
    assert response.status_code == 400
    assert "Missing required fields" in response.get_data(as_text=True)

def test_usage_invalid_start_format(client):
    response = client.get("/usage?start=not-a-timestamp&end=2025-04-10T00:00:00Z")
    assert response.status_code == 400
    assert "Invalid 'start'" in response.get_data(as_text=True)

def test_usage_invalid_end_format(client):
    response = client.get("/usage?start=2025-04-09T00:00:00Z&end=invalid-end")
    assert response.status_code == 400
    assert "Invalid 'end'" in response.get_data(as_text=True)