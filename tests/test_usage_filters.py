import pytest
from measure import create_app, db
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote

from measure.models import APIUsageEvent

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
            db.session.remove()
            db.drop_all()

@pytest.fixture
def seed_events():
    now = datetime.now(pytz.UTC)
    return [
        APIUsageEvent(account_id="acct_1", endpoint="/api/test", timestamp=now - timedelta(days=1)),
        APIUsageEvent(account_id="acct_2", endpoint="/api/test", timestamp=now),
        APIUsageEvent(account_id="acct_1", endpoint="/api/other", timestamp=now + timedelta(days=1)),
    ]

def test_usage_valid_range(client, seed_events):
    with app.app_context():
        db.session.bulk_save_objects(seed_events)
        db.session.commit()

    start = quote((datetime.now(pytz.UTC) - timedelta(days=2)).isoformat())
    end = quote((datetime.now(pytz.UTC) + timedelta(days=2)).isoformat())

    resp = client.get(f"/usage?start={start}&end={end}")
    assert resp.status_code == 200
    assert isinstance(resp.json, list)
    assert len(resp.json) == 3  # all match

def test_usage_missing_start(client):
    resp = client.get("/usage?end=2025-04-10T00:00:00Z")
    assert resp.status_code == 400
    assert "Missing required fields" in resp.get_data(as_text=True)

def test_usage_missing_end(client):
    resp = client.get("/usage?start=2025-04-08T00:00:00Z")
    assert resp.status_code == 400
    assert "Missing required fields" in resp.get_data(as_text=True)

def test_usage_with_account_filter(client, seed_events):
    with app.app_context():
        db.session.bulk_save_objects(seed_events)
        db.session.commit()

    now = datetime.now(pytz.UTC)
    start = quote((now - timedelta(days=2)).isoformat())
    end = quote((now + timedelta(days=2)).isoformat())

    resp = client.get(f"/usage?start={start}&end={end}&account_id=acct_1")
    assert resp.status_code == 200
    assert all(row["account_id"] == "acct_1" for row in resp.json)
    assert len(resp.json) == 2

def test_usage_with_endpoint_filter(client, seed_events):
    with app.app_context():
        db.session.bulk_save_objects(seed_events)
        db.session.commit()

    now = datetime.now(pytz.UTC)
    start = quote((now - timedelta(days=2)).isoformat())
    end = quote((now + timedelta(days=2)).isoformat())

    resp = client.get(f"/usage?start={start}&end={end}&endpoint=/api/test")
    assert resp.status_code == 200
    assert all(row["endpoint"] == "/api/test" for row in resp.json)
    assert len(resp.json) == 2

def test_usage_with_all_filters(client, seed_events):
    with app.app_context():
        db.session.bulk_save_objects(seed_events)
        db.session.commit()

    now = datetime.now(pytz.UTC)
    start = quote((now - timedelta(days=2)).isoformat())
    end = quote((now + timedelta(days=2)).isoformat())

    resp = client.get(f"/usage?start={start}&end={end}&account_id=acct_1&endpoint=/api/test")
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["account_id"] == "acct_1"
    assert resp.json[0]["endpoint"] == "/api/test"

def test_usage_returns_empty(client, seed_events):
    with app.app_context():
        db.session.bulk_save_objects(seed_events)
        db.session.commit()

    # Set a start/end range in the far past
    start = quote((datetime(2000, 1, 1, tzinfo=pytz.UTC)).isoformat())
    end = quote((datetime(2000, 1, 2, tzinfo=pytz.UTC)).isoformat())

    resp = client.get(f"/usage?start={start}&end={end}")
    assert resp.status_code == 200
    assert resp.json == []
