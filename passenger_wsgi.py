import sys
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(__file__)

# Add app folder to path
sys.path.insert(0, os.path.join(BASE_DIR, 'app'))

# Load .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Activate virtualenv (VERY IMPORTANT on cPanel)
VENV_PATH = "/home/farmsglo/virtualenv/halimatu/3.12/bin/activate_this.py"
with open(VENV_PATH) as f:
    exec(f.read(), dict(__file__=VENV_PATH))

# Import FastAPI app
from main import app

# Convert ASGI → WSGI for Passenger
from asgiref.wsgi import WsgiToAsgi

application = WsgiToAsgi(app)