import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import QueuePool
from sqlalchemy import func
from datetime import datetime
from dateutil import parser
import pytz

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://masurel:masurel@localhost:5432/measure?connect_timeout=3'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://measure:measure@xxx:5432/xxxure?connect_timeout=3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# TODO: We need to explore more and figure out the best possible parameters for our usage to optimally use the connection pool.
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "poolclass": QueuePool,
    "pool_size": 10,           # Number of persistent connections
    "max_overflow": 20,        # Extra connections on demand (temporary)
    "pool_timeout": 5,         # Seconds to wait for a connection before failing
    "pool_recycle": 1800       # Recycle connections every 30 min to avoid stale issues
}

db = SQLAlchemy(app)


# Initialize limiter, currently this does not support rate limit per account_id
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per minute"],  # global default
    storage_uri="memory://",  # For production: use Redis
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            db.session.execute("SELECT 1")  # test connection
            logger.info("Successfully connected to the database.")
        except Exception as e:
            logger.exception("Failed to connect to the database on startup")

class APIUsageEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(80), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.UTC))

    def to_dict(self):
        return {
            'account_id': self.account_id,
            'endpoint': self.endpoint,
            'timestamp': self.timestamp.isoformat()
        }

def get_account_id():
    try:
        data = request.get_json(silent=True) or {}
        return data.get("account_id", "anonymous")
    except Exception:
        return "anonymous"

# API to log a single event with required fields: account_id, endpoint, timestamp
# Stores the usage record in the database with UTC-normalized timestamp
@app.route("/log-event", methods=["POST"])
@limiter.limit("1 per minute", key_func=get_account_id)
def log_event():
    try:
        data = request.get_json()
        logger.debug(f"Received /log-event payload: {data}")

        if not all(k in data for k in ["account_id", "endpoint", "timestamp"]):
            logger.warning("Missing required fields in /log-event")
            return jsonify({"error": "Missing required fields: account_id, endpoint, timestamp"}), 400

        timestamp = parser.isoparse(data["timestamp"]).astimezone(pytz.UTC)
        event = APIUsageEvent(
            account_id=data["account_id"],
            endpoint=data["endpoint"],
            timestamp=timestamp
        )
        logger.debug(f"Attempting to save event: {event.to_dict()}")
        db.session.add(event)
        db.session.commit()
        logger.info("Logged event successfully")
        return jsonify({"message": "Event logged"}), 201

    except Exception as e:
        logger.exception("Internal server error in /log-event")
        return jsonify({"error": "Internal server error"}), 500


# API to query usage data
# Supports filtering by account_id, endpoint, and time range (start & end in ISO format)
# Returns aggregated usage count grouped by (account_id, endpoint)
# API to query usage data
# Requires start time. End time is optional. Both start and end are inclusive.
@app.route("/usage", methods=["GET"])
@limiter.limit("10 per second", key_func=get_account_id)
def usage():
    try:
        account_id = request.args.get("account_id")
        endpoint = request.args.get("endpoint")
        start = request.args.get("start")
        end = request.args.get("end")

        if not start or not end:
            logger.warning("Missing required fields in /usage")
            return jsonify({"error": "Missing required fields: start, end"}), 400

        logger.debug(f"Received /usage query with account_id={account_id}, endpoint={endpoint}, start={start}, end={end}")

        query = db.session.query(APIUsageEvent)

        if start:
            try:
                start_time = parser.isoparse(start).replace(tzinfo=pytz.UTC)
                query = query.filter(APIUsageEvent.timestamp >= start_time)
            except ValueError:
                logger.warning(f"Invalid 'start' parameter: {start}")
                return jsonify({"error": "Invalid 'start' parameter format. Please use ISO 8601 format."}), 400

        if end:
            try:
                end_time = parser.isoparse(end).replace(tzinfo=pytz.UTC)
                query = query.filter(APIUsageEvent.timestamp <= end_time)
            except ValueError:
                logger.warning(f"Invalid 'end' parameter: {end}")
                return jsonify({"error": "Invalid 'end' parameter format. Please use ISO 8601 format."}), 400

        if account_id:
            query = query.filter(APIUsageEvent.account_id == account_id)

        if endpoint:
            query = query.filter(APIUsageEvent.endpoint == endpoint)

        results = query.all()

        response = [event.to_dict() for event in results]
        logger.debug(f"/usage response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.exception("Internal server error in /usage")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    logger.debug("Root endpoint hit")
    return f"Hello {name}!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
