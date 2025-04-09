import pytest
from main import app, db, APIUsageEvent
from datetime import datetime, timedelta
import pytz

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

@pytest.fixture
def seed_data():
    now = datetime.now(pytz.UTC)
    earlier = now - timedelta(days=1)
    later = now + timedelta(days=1)
    return [
        APIUsageEvent(account_id='acct1', endpoint='/api/one', timestamp=earlier),
        APIUsageEvent(account_id='acct2', endpoint='/api/two', timestamp=now),
        APIUsageEvent(account_id='acct1', endpoint='/api/one', timestamp=later),
    ]

def test_account_id_filter(client, seed_data):
    with app.app_context():
        db.session.bulk_save_objects(seed_data)
        db.session.commit()

    resp = client.get("/usage?account_id=acct2")
    assert resp.status_code == 200
    results = resp.get_json()
    assert all(r['account_id'] == 'acct2' for r in results)
    assert len(results) == 1

def test_endpoint_filter(client, seed_data):
    with app.app_context():
        db.session.bulk_save_objects(seed_data)
        db.session.commit()

    resp = client.get("/usage?endpoint=/api/two")
    assert resp.status_code == 200
    results = resp.get_json()
    assert all(r['endpoint'] == '/api/two' for r in results)
    assert len(results) == 1

def test_start_filter(client, seed_data):
    with app.app_context():
        db.session.bulk_save_objects(seed_data)
        db.session.commit()

    now = datetime.now(pytz.UTC).isoformat()
    resp = client.get(f"/usage?start={now}")
    assert resp.status_code == 200
    results = resp.get_json()
    assert all(parser.isoparse(r['timestamp']) >= parser.isoparse(now) for r in results)

def test_end_filter(client, seed_data):
    with app.app_context():
        db.session.bulk_save_objects(seed_data)
        db.session.commit()

    now = datetime.now(pytz.UTC).isoformat()
    resp = client.get(f"/usage?end={now}")
    assert resp.status_code == 200
    results = resp.get_json()
    assert all(parser.isoparse(r['timestamp']) <= parser.isoparse(now) for r in results)
