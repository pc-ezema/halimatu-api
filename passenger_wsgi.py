import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from main import app as application