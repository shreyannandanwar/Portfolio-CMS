import os
from app import create_app

# Gunicorn imports this module and uses `app` as the WSGI callable.
# The env var lets you switch without touching code.
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    # Only used locally — never run with debug=True in production.
    app.run(debug=(env == 'development'))