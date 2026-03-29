import sys
import os
from a2wsgi import ASGIMiddleware

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI app
from app.main import app

# Wrap the FastAPI (ASGI) app with ASGIMiddleware to make it WSGI compatible
application = ASGIMiddleware(app)