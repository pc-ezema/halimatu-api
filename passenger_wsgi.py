import os
import sys
import traceback

# -------------------------------
# 1. Project root & sys.path setup
# -------------------------------
project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, project_root)

# -------------------------------
# 2. Environment detection (default to production)
# -------------------------------
# You can manually set APP_ENV in Passenger config if you want dev mode
ENV = os.getenv("APP_ENV", "production").lower()
IS_DEV = ENV in ("dev", "development", "local")

# -------------------------------
# 3. Logging function
# -------------------------------
def log_error(e):
    log_file = os.path.join(project_root, 'wsgi_error.log')
    with open(log_file, 'a') as f:
        f.write("----- WSGI Startup Error -----\n")
        f.write(traceback.format_exc())
        f.write("\n------------------------------\n")

# -------------------------------
# 4. Load FastAPI app safely
# -------------------------------
try:
    from a2wsgi import ASGIMiddleware
    from app.main import app  # Your FastAPI app
    application = ASGIMiddleware(app)

except Exception as e:
    if IS_DEV:
        # Show full traceback in dev mode
        def application(environ, start_response):
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [traceback.format_exc().encode()]
    else:
        # Log error and show generic message in production
        log_error(e)
        def application(environ, start_response):
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [b"An internal server error occurred. Please try again later."]