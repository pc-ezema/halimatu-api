import sys
import os

# Add your app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from asgiref.wsgi import WsgiToAsgi
from app.main import app  # your FastAPI app

application = WsgiToAsgi(app)