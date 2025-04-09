from datetime import datetime
import pytz
from . import db

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