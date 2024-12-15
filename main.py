from database.db import create_tables
from database.models import *
from wsgiref.simple_server import make_server
from app.routes import app

def main():
    try:
        create_tables()
        print("Tables created!")
    except Exception as e:
        print(f"Error occured {e}")
    with make_server('', 8000, app) as httpd:
        print('Serving on port 8000...')

        # Serve until process is killed
        httpd.serve_forever()

if __name__ == "__main__":
    main()
