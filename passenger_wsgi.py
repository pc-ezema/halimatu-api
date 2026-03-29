import sys
import os

# Add the 'app' directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import your Flask app
from main import app as application  # 'app' is your Flask instance