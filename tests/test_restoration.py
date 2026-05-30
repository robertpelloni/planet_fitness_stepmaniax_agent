import unittest
import os
import sqlite3
import shutil
from backup_job import run_backup

class TestRestoration(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_crm_restore.db'
        self.test_backup_dir = 'test_backups_restore'
        self.restored_db = 'restored_test_crm.db'

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE important_data (id INTEGER PRIMARY KEY, content TEXT)')
        cursor.execute('INSERT INTO important_data (content) VALUES ("critical info")')
        cursor.execute('CREATE TABLE automation_heartbeat (id INTEGER PRIMARY KEY, task_name TEXT UNIQUE, last_run TEXT, status TEXT)')
        conn.commit()
        conn.close()

        if not os.path.exists(self.test_backup_dir):
            os.makedirs(self.test_backup_dir)

        import backup_job
        self.original_db_path = backup_job.DB_PATH
        self.original_backup_dir = backup_job.BACKUP_DIR
        backup_job.DB_PATH = os.path.abspath(self.test_db)
        backup_job.BACKUP_DIR = os.path.abspath(self.test_backup_dir)

    def tearDown(self):
        import backup_job
        backup_job.DB_PATH = self.original_db_path
        backup_job.BACKUP_DIR = self.original_backup_dir

        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.restored_db):
            os.remove(self.restored_db)
        if os.path.exists(self.test_backup_dir):
            shutil.rmtree(self.test_backup_dir)

    def test_restoration_integrity(self):
        """Verify that a backup can be 'restored' and contains the original data."""
        run_backup()
        backups = os.listdir(self.test_backup_dir)
        backup_file = os.path.join(self.test_backup_dir, backups[0])
        shutil.copy2(backup_file, self.restored_db)

        conn = sqlite3.connect(self.restored_db)
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM important_data')
        row = cursor.fetchone()
        self.assertEqual(row[0], "critical info")
        conn.close()

if __name__ == '__main__':
    unittest.main()
