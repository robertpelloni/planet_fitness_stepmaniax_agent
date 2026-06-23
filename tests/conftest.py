import pytest
import subprocess
import time
import requests
import sqlite3
import os

@pytest.fixture(scope="session", autouse=True)
def start_gunicorn():
    os.system("python fix_db.py")
    os.system("python -c \"from app import app; from models import db; app.app_context().push(); db.create_all()\"")
    os.system("python populate_test_data.py")

    os.system("kill $(lsof -t -i :5000) 2>/dev/null || true")
    time.sleep(1)

    print("Starting Gunicorn...")
    proc = subprocess.Popen(["python", "-m", "gunicorn", "-w", "1", "-b", "127.0.0.1:5000", "app:app"],
                            stdout=open('test_gunicorn.log', 'w'), stderr=subprocess.STDOUT)

    for _ in range(15):
        try:
            response = requests.get("http://127.0.0.1:5000/login", timeout=1)
            if response.status_code == 200:
                print("Gunicorn is ready!")
                break
        except Exception:
            pass
        time.sleep(1)

    yield
    print("Terminating Gunicorn...")
    proc.terminate()
    proc.wait()
