from werkzeug.exceptions import BadRequest
from flask import request
from dateutil import parser
import pytz
import logging

def parse_utc(iso_str):
    dt = parser.isoparse(iso_str)
    if dt.tzinfo is None:
        return pytz.UTC.localize(dt)
    return dt.astimezone(pytz.UTC)

def get_account_id():
    try:
        data = request.get_json(silent=True) or {}
        return data.get("account_id", "anonymous")
    except Exception:
        return "anonymous"

def validate_timestamp(timestamp_str, label):
    try:
        dt = parser.isoparse(timestamp_str)
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        else:
            dt = dt.astimezone(pytz.UTC)
        return dt
    except Exception:
        logging.warning(f"Invalid '{label}' timestamp format")
        raise BadRequest(f"Invalid '{label}' timestamp format. Use ISO 8601 with timezone info.")