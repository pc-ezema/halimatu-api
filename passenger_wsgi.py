import sys
import os

# Add project root to sys.path
cwd = os.getcwd()
sys.path.append(cwd)

# Make sure Python uses the correct virtualenv (set in cPanel / Passenger settings)
# No activate_this.py needed in Python 3.12

# Import the FastAPI app
from app.main import app as application