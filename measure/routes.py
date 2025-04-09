from flask import request, jsonify
from . import db, limiter
from .models import APIUsageEvent
from werkzeug.exceptions import BadRequest
from .utils import parse_utc, get_account_id, validate_timestamp
import logging

def register_routes(app):
    @app.route("/")
    def hello_world():
        name = request.args.get("NAME", "World")
        return f"Hello {name}!"

    @app.route("/log-event", methods=["POST"])
    @limiter.limit("10 per second", key_func=get_account_id)
    def log_event():
        try:
            data = request.get_json()
            if not all(k in data for k in ["account_id", "endpoint", "timestamp"]):
                return jsonify({"error": "Missing required fields"}), 400

            timestamp = parse_utc(data["timestamp"])
            validate_timestamp(timestamp, "timestamp")

            event = APIUsageEvent(account_id=data["account_id"], endpoint=data["endpoint"], timestamp=timestamp)
            db.session.add(event)
            db.session.commit()
            return jsonify({"message": "Event logged"}), 201
        except BadRequest as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            logging.exception("log_event failed")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/usage", methods=["GET"])
    @limiter.limit("10 per second", key_func=get_account_id)
    def usage():
        try:
            account_id = request.args.get("account_id")
            endpoint = request.args.get("endpoint")
            start = request.args.get("start")
            end = request.args.get("end")

            if not start or not end:
                return jsonify({"error": "Missing required fields: start, end"}), 400

            validate_timestamp(start, "start")
            validate_timestamp(end, "end")

            query = db.session.query(APIUsageEvent)
            query = query.filter(APIUsageEvent.timestamp >= parse_utc(start))
            query = query.filter(APIUsageEvent.timestamp <= parse_utc(end))
            if account_id:
                query = query.filter(APIUsageEvent.account_id == account_id)
            if endpoint:
                query = query.filter(APIUsageEvent.endpoint == endpoint)

            return jsonify([e.to_dict() for e in query.all()])
        except BadRequest as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            logging.exception("usage query failed")
            return jsonify({"error": "Internal server error"}), 500
