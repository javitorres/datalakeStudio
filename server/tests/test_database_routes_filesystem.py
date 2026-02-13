import io
import json
import os
import tempfile
import unittest

import duckdb
from fastapi import UploadFile

from routes import database_controller
from services import databaseService


class _FakeServerStatus:
    def __init__(self, config, current_db):
        self._config = config
        self._status = {"currentDatabase": current_db}

    def getConfig(self):
        return self._config

    def get(self):
        return self._status

    def setCurrentDatabase(self, databaseName):
        self._status["currentDatabase"] = databaseName


class DatabaseRoutesFilesystemTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_folder = os.path.join(self.tmp.name, "db")
        self.download_folder = os.path.join(self.tmp.name, "tmp")
        os.makedirs(self.db_folder, exist_ok=True)
        os.makedirs(self.download_folder, exist_ok=True)

        # Seed existing DB files.
        duckdb.connect(os.path.join(self.db_folder, "main.db")).close()
        duckdb.connect(os.path.join(self.db_folder, "aux.db")).close()

        # In-memory connection for table-level tests.
        databaseService.db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})

        self.original_server_status = database_controller.serverStatus
        self.fake_status = _FakeServerStatus(
            {
                "databasesFolder": self.db_folder,
                "downloadFolder": self.download_folder,
            },
            current_db="main",
        )
        database_controller.serverStatus = self.fake_status

        # Avoid extension/network loading when switching DBs.
        self.original_load_extensions = databaseService.loadExtensions
        databaseService.loadExtensions = lambda secrets: None
        databaseService.secretsLoaded = {}

    def tearDown(self):
        database_controller.serverStatus = self.original_server_status
        databaseService.loadExtensions = self.original_load_extensions
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
        self.assertTrue(os.path.exists(os.path.join(self.db_folder, "newdb.db")))

    def test_change_database_updates_server_status(self):
        # Ensure target exists without touching runtime DB.
        duckdb.connect(os.path.join(self.db_folder, "target.db")).close()

        out = database_controller.changeDatabase("target")
        self.assertEqual(out["status"], "ok")
        self.assertEqual(self.fake_status.get()["currentDatabase"], "target")

    def test_export_data_writes_csv(self):
        databaseService.db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})
        databaseService.runQuery("CREATE TABLE t AS SELECT 1 AS id, 'x' AS label")

        out_file = os.path.join(self.tmp.name, "export.csv")
        resp = database_controller.exportData("t", "csv", out_file)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(os.path.exists(out_file))

        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("id,label", content)

    def test_upload_file_creates_table(self):
        databaseService.db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})

        payload = b"id,name\n1,Ana\n2,Bob\n"
        upload = UploadFile(filename="people.csv", file=io.BytesIO(payload))

        out = database_controller.uploadFile(file=upload, tableName="people")
        self.assertEqual(out["status"], "ok")

        count = databaseService.runQuery("SELECT COUNT(*) AS c FROM people")
        self.assertEqual(int(count["c"].iloc[0]), 2)


if __name__ == '__main__':
    unittest.main()
