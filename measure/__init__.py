import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri="memory://")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    limiter.init_app(app)

    from .routes import register_routes
    register_routes(app)

    with app.app_context():
        from .models import APIUsageEvent
        db.create_all()
        logging.info("Successfully connected to the database.")

    return app
