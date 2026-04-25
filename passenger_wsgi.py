import sys
import os

project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, project_root)

from asgiref.wsgi import AsgiToWsgi
from app.main import app

application = AsgiToWsgi(app)