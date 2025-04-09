from datetime import datetime

from flask import request, jsonify
from . import db, limiter
from .models import APIUsageEvent
from werkzeug.exceptions import BadRequest
from .utils import parse_utc, get_account_id, validate_timestamp
import logging
import pytz


def call_nango_slack(e):
    # TODO(lahiru): Integrate with Nango and send a message.
    logging.error("call_nango_slack invoked")
    return jsonify(error="Rate limit exceeded. Try again later."), 429


limiter._on_breach = call_nango_slack


def register_routes(app):

    @app.route("/log-event", methods=["POST"])
    @limiter.limit("1 per minute", key_func=get_account_id)
    def log_event():
        """
            Logs an API usage event. The event includes the account ID, the endpoint accessed, and the timestamp.

            **Request Body**:
            - `account_id` (string): The account ID associated with the API call (required).
            - `endpoint` (string): The API endpoint being accessed (required).
            - `timestamp` (string, ISO 8601): The timestamp of the event (required).

            **Response**:
            - If successful: Returns a message confirming the event was logged.
            - If there are missing fields or invalid timestamp format: Returns a 400 error with an error message.
            - If timestamp is in the future: Returns a 400 error with a message indicating the timestamp cannot be in the future.
            - If there’s an internal server error: Returns a 500 error.

            **Example**:
            ```
            {
                "account_id": "acct_1",
                "endpoint": "/api/v1/feature",
                "timestamp": "2025-04-09T12:34:56.789123+00:00"
            }
            ```

            **Error Handling**:
            - 400 Bad Request: Missing required fields or invalid timestamp format.
            - 500 Internal Server Error: When an unexpected error occurs while processing the request.
        """
        try:
            data = request.get_json()
            if not all(k in data for k in ["account_id", "endpoint", "timestamp"]):
                return jsonify({"error": "Missing required fields"}), 400

            timestamp = parse_utc(data["timestamp"])
            validate_timestamp(data["timestamp"], "timestamp")
            if timestamp > datetime.now(pytz.UTC):
                logging.warning("Timestamp is in the future")
                return jsonify({"error": "Timestamp cannot be in the future."}), 400

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
    @limiter.limit("50 per second", key_func=get_account_id)
    def usage():
        """
            Queries the API usage data for a given account and endpoint, filtered by a time range (start and end).

            **Query Parameters**:
            - `account_id` (string, optional): The account ID for filtering events (optional).
            - `endpoint` (string, optional): The API endpoint for filtering events (optional).
            - `start` (string, ISO 8601, required): The start time for the time range (required).
            - `end` (string, ISO 8601, required): The end time for the time range (required).
            
            **Response**:
            - Returns a list of events matching the query criteria, including account_id, endpoint, and timestamp.
            - If `start` or `end` is missing: Returns a 400 error with a message indicating that both are required.
            - If `start` or `end` timestamp format is invalid: Returns a 400 error with a message indicating the invalid timestamp format.
            - If there’s an internal server error: Returns a 500 error.

            **Example**:
            ```
            GET /usage?start=2025-04-08T00:00:00Z&end=2025-04-09T00:00:00Z&account_id=acct_1
            ```

            **Error Handling**:
            - 400 Bad Request: Missing `start` or `end` parameters or invalid timestamp format.
            - 500 Internal Server Error: When an unexpected error occurs while processing the request.
        """
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
