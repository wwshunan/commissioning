from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sqlalchemy import db, declarative_base
from flask_redis import FlaskRedis
from .celery_utils import init_celery
from .config import Config
import os

PKG_NAME = os.path.dirname(os.path.realpath(__file__)).split("/")[-1]
db = SQLAlchemy()
Base = declarative_base()
cache = Cache()
redis_client = FlaskRedis()

def create_app(app_name=PKG_NAME, **kwargs):
    app = Flask(app_name)
    app.config.from_object(Config)
    db.init_app(app)
    cache.init_app(app)
    redis_client.init_app(app)
    CORS(app)
    if 'celery' in kwargs:
        init_celery(kwargs.get('celery'), app)

    from .views import bp
    app.register_blueprint(bp)
    return app