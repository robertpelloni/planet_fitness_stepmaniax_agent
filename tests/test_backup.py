import unittest
import os
import sqlite3
import shutil
from backup_job import run_backup

class TestBackupJob(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_crm.db'
        self.test_backup_dir = 'test_backups'

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)')
        cursor.execute('INSERT INTO test (data) VALUES ("test data")')
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
        if os.path.exists(self.test_backup_dir):
            shutil.rmtree(self.test_backup_dir)

    def test_run_backup_success(self):
        """Verify that run_backup creates a valid database file."""
        success = run_backup()
        self.assertTrue(success)

        backups = os.listdir(self.test_backup_dir)
        self.assertEqual(len(backups), 1)
        backup_file = os.path.join(self.test_backup_dir, backups[0])

        conn = sqlite3.connect(backup_file)
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM test')
        row = cursor.fetchone()
        self.assertEqual(row[0], "test data")
        conn.close()

if __name__ == '__main__':
    unittest.main()
