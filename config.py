import os
from sqlalchemy.pool import QueuePool

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://masurel:masurel@127.0.0.1:5432/measure?connect_timeout=3'
        # 'postgresql://measure:measure@34.121.211.245:5432/measure?connect_timeout=3'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": QueuePool,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 5,
        "pool_recycle": 1800
    }
