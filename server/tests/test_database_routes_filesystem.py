import io
import json
import os
import tempfile
import unittest

import duckdb
from fastapi import UploadFile

from routes import database_controller
from services import databaseService

TEST_USER = "test_user"


class DatabaseRoutesFilesystemTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_folder = os.path.join(self.tmp.name, "db")
        self.user_db_folder = os.path.join(self.db_folder, TEST_USER)
        self.download_folder = os.path.join(self.tmp.name, "tmp")
        os.makedirs(self.user_db_folder, exist_ok=True)
        os.makedirs(self.download_folder, exist_ok=True)

        # Seed existing DB files in user folder.
        duckdb.connect(os.path.join(self.user_db_folder, "main.db")).close()
        duckdb.connect(os.path.join(self.user_db_folder, "aux.db")).close()

        # Configure databaseService for testing.
        databaseService._config = {
            "databasesFolder": self.db_folder,
            "downloadFolder": self.download_folder,
            "defaultDatabase": "main.db",
        }
        databaseService.set_current_user(TEST_USER)
        db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})
        databaseService._connections[TEST_USER] = {"main.db": db}
        databaseService._active_db[TEST_USER] = "main.db"

        # Avoid extension/network loading when switching DBs.
        self.original_load_extensions = databaseService._load_extensions_for_db
        databaseService._load_extensions_for_db = lambda db: None

    def tearDown(self):
        databaseService._load_extensions_for_db = self.original_load_extensions
        # Clean up user state
        databaseService._connections.pop(TEST_USER, None)
        databaseService._active_db.pop(TEST_USER, None)
        self.tmp.cleanup()

    @staticmethod
    def _json(response):
        return json.loads(response.body.decode('utf-8'))

    def test_get_database_list_prioritizes_current(self):
        resp = database_controller.getDatabaseList()
        self.assertEqual(resp.status_code, 200)

        body = self._json(resp)
        self.assertEqual(body[0], "main")
        self.assertIn("aux", body)
        self.assertEqual(resp.headers.get("x-current-database"), "main")

    def test_create_database_creates_file(self):
        out = database_controller.createDatabase("newdb.db")
        self.assertEqual(out["status"], "ok")
        self.assertTrue(os.path.exists(os.path.join(self.user_db_folder, "newdb.db")))

    def test_change_database_updates_server_status(self):
        # Ensure target exists in user folder.
        duckdb.connect(os.path.join(self.user_db_folder, "target.db")).close()

        out = database_controller.changeDatabase("target")
        self.assertEqual(out["status"], "ok")
        self.assertEqual(databaseService.get_current_database_name(), "target")

    def test_export_data_writes_csv(self):
        databaseService.runQuery("CREATE TABLE t AS SELECT 1 AS id, 'x' AS label")

        out_file = os.path.join(self.tmp.name, "export.csv")
        resp = database_controller.exportData("t", "csv", out_file)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(os.path.exists(out_file))

        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("id,label", content)

    def test_upload_file_creates_table(self):
        payload = b"id,name\n1,Ana\n2,Bob\n"
        upload = UploadFile(filename="people.csv", file=io.BytesIO(payload))

        out = database_controller.uploadFile(file=upload, tableName="people")
        self.assertEqual(out["status"], "ok")

        count = databaseService.runQuery("SELECT COUNT(*) AS c FROM people")
        self.assertEqual(int(count["c"].iloc[0]), 2)


if __name__ == '__main__':
    unittest.main()
