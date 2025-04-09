from flask import request

def get_account_id():
    try:
        data = request.get_json(silent=True) or {}
        return data.get("account_id", "anonymous")
    except Exception:
        return "anonymous"