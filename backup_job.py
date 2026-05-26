import sqlite3
import os
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
        source = sqlite3.connect(DB_PATH)
        dest = sqlite3.connect(backup_file)
        with dest:
            source.backup(dest)
        source.close()
        dest.close()
        print(f"[{datetime.now()}] Backup successful: {backup_file}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Backup failed: {e}")
        return False

if __name__ == "__main__":
    run_backup()
