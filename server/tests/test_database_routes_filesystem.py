import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import duckdb
import pandas as pd
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
        for db in databaseService._connections.pop(TEST_USER, {}).values():
            db.close()
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

        resp = database_controller.exportData("t", "csv")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.path, os.path.join(self.download_folder, TEST_USER, "t.csv"))

        with open(resp.path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("id,label", content)

    def test_export_file_stays_in_the_temp_folder(self):
        databaseService.runQuery('CREATE TABLE "../escaped" AS SELECT 1 AS id')

        resp = database_controller.exportData('"../escaped"', "parquet")
        self.assertEqual(os.path.dirname(resp.path), os.path.join(self.download_folder, TEST_USER))
        self.assertEqual(database_controller.exportData("t", "xlsx").status_code, 400)

    def test_database_names_cannot_leave_the_user_folder(self):
        other_db = os.path.join(self.db_folder, "other_user", "secret.db")
        os.makedirs(os.path.dirname(other_db))
        duckdb.connect(other_db).close()

        resp = database_controller.changeDatabase("../other_user/secret")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(databaseService.get_current_database_name(), "main")

        resp = database_controller.createDatabase("../../outside.db")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "outside.db")))

    def test_upload_file_name_cannot_leave_the_temp_folder(self):
        upload = UploadFile(filename="../../escaped.csv", file=io.BytesIO(b"id\n1\n"))

        with patch.object(databaseService, "loadTable", return_value=False) as load_table:
            database_controller.uploadFile(file=upload, tableName="escaped")
        self.assertEqual(load_table.call_args.args[1], os.path.join(self.download_folder, TEST_USER, "escaped.csv"))
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "escaped.csv")))

    def test_loading_a_local_file_outside_the_temp_folder(self):
        source = os.path.join(self.tmp.name, "keep.csv")
        with open(source, "w", encoding="utf-8") as f:
            f.write("id\n1\n")

        # Sandbox on: refused and left untouched
        self.assertFalse(databaseService.loadTable("blocked", source))
        self.assertTrue(os.path.exists(source))

        # Sandbox off (single user): loaded, and still never deleted
        databaseService._config["sandboxEnabled"] = False
        self.assertTrue(databaseService.loadTable("kept", source))
        self.assertTrue(os.path.exists(source))

    def test_sandbox_confines_sql_to_the_user_folders(self):
        other_db = os.path.join(self.db_folder, "other_user", "secret.db")
        os.makedirs(os.path.dirname(other_db))
        duckdb.connect(other_db).close()
        outside_csv = os.path.join(self.tmp.name, "outside.csv")
        own_csv = os.path.join(databaseService.get_user_temp_folder(), "own.csv")
        for path in (outside_csv, own_csv):
            with open(path, "w", encoding="utf-8") as f:
                f.write("a\n1\n")

        database_controller.changeDatabase("aux")  # opens a sandboxed connection

        self.assertEqual(len(databaseService.runQuery(f"SELECT * FROM read_csv('{own_csv}')")), 1)
        databaseService.createTableFromDataFrame(pd.DataFrame({"id": [1, 2]}), "from_df")
        for blocked in (f"SELECT * FROM read_csv('{outside_csv}')",
                        f"ATTACH '{other_db}' AS other",
                        f"COPY (SELECT 1) TO '{os.path.join(self.tmp.name, 'written.csv')}'",
                        "SET enable_external_access = true"):
            with self.assertRaises(Exception, msg=blocked):
                databaseService.runQuery(blocked, False)

    def test_upload_file_creates_table(self):
        payload = b"id,name\n1,Ana\n2,Bob\n"
        upload = UploadFile(filename="people.csv", file=io.BytesIO(payload))

        out = database_controller.uploadFile(file=upload, tableName="people")
        self.assertEqual(out["status"], "ok")

        count = databaseService.runQuery("SELECT COUNT(*) AS c FROM people")
        self.assertEqual(int(count["c"].iloc[0]), 2)


if __name__ == '__main__':
    unittest.main()
