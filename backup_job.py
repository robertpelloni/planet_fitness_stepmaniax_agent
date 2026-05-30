import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm.db')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

def run_backup():
    """
    Creates a timestamped backup of the SQLite database.
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"crm_backup_{timestamp}.db")

    try:
        # Using sqlite3's backup API for a safe online backup
        source = sqlite3.connect(DB_PATH)
        dest = sqlite3.connect(backup_file)
        with dest:
            source.backup(dest)
        source.close()
        dest.close()

        print(f"[{datetime.now()}] Backup successful: {backup_file}")

        # Log to heartbeat
        log_heartbeat('Database Backup', 'Healthy')
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Backup failed: {e}")
        log_heartbeat('Database Backup', f'Failed: {e}')
        return False

def log_heartbeat(task_name, status):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO automation_heartbeat (task_name, last_run, status)
            VALUES (?, ?, ?)
            ON CONFLICT(task_name) DO UPDATE SET last_run=excluded.last_run, status=excluded.status
        """, (task_name, timestamp, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log heartbeat for {task_name}: {e}")

if __name__ == "__main__":
    run_backup()
