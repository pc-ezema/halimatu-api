import os
import sys

# Get the absolute path of the current directory
project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, project_root)

# Try to import. If this fails, it shows in the error log.
try:
    from a2wsgi import ASGIMiddleware
    from app.main import app
    application = ASGIMiddleware(app)
except Exception as e:
    # This prevents the "infinite hang" by crashing immediately with the real error
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [f"Error during import: {str(e)}".encode()]