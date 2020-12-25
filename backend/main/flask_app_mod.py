from . import factory, celery
from flask_socketio import SocketIO
import eventlet

eventlet.monkey_patch()
app = factory.create_app(celery=celery)
socket_io = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

