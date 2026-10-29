import gzip
import io
import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

import duckdb
import pandas as pd
from fastapi import UploadFile

from model.QueryRequestDTO import QueryRequest
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
        with self.assertRaises(ValueError):
            databaseService.loadTable("blocked", source)
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

    def test_load_errors_are_reported_with_their_reason(self):
        for name, content, reason in [("notes.txt", b"hello", "unsupported file type: notes.txt"),
                                      ("broken.parquet", b"not parquet", "parquet")]:
            upload = UploadFile(filename=name, file=io.BytesIO(content))

            resp = database_controller.uploadFile(file=upload, tableName="t")
            self.assertEqual(resp.status_code, 400, name)
            self.assertIn(reason, self._json(resp)["message"].lower())
            self.assertFalse(os.path.exists(os.path.join(self.download_folder, TEST_USER, name)))

    def test_compressed_csv_and_json_are_loaded(self):
        for name, content in [("sales.csv.gz", b"id,city\n1,Madrid\n"),
                              ("events.json.gz", b'[{"id": 1, "city": "Madrid"}]')]:
            table = name.split(".")[0]
            upload = UploadFile(filename=name, file=io.BytesIO(gzip.compress(content)))

            out = database_controller.uploadFile(file=upload, tableName=table)
            self.assertEqual(out["status"], "ok", name)
            self.assertEqual(databaseService.runQuery(f"SELECT city FROM {table}")["city"].to_list(), ["Madrid"])

    def test_spatial_files_load_for_users_with_a_dot_in_their_name(self):
        user = "ana.garcia@example.com"
        databaseService.set_current_user(user)
        databaseService._connections[user] = {"main.db": duckdb.connect(':memory:')}
        databaseService._active_db[user] = "main.db"
        geojson = json.dumps({"type": "FeatureCollection", "features": [{
            "type": "Feature", "properties": {"name": "Madrid"},
            "geometry": {"type": "Point", "coordinates": [-3.7, 40.4]}}]}).encode()
        try:
            try:
                databaseService.runQuery("INSTALL spatial; LOAD spatial;", False)
                spatial = True
            except Exception:
                spatial = False

            out = database_controller.uploadFile(file=UploadFile(filename="parcels.geojson", file=io.BytesIO(geojson)),
                                                 tableName="parcels")
            if spatial:
                self.assertEqual(out["status"], "ok")
            else:
                # Without the extension the load fails, but in ST_Read: the file type was recognised
                self.assertNotIn("Unsupported file type", self._json(out)["message"])
        finally:
            for db in databaseService._connections.pop(user, {}).values():
                db.close()
            databaseService._active_db.pop(user, None)
            databaseService._last_used.pop((user, "main.db"), None)
            databaseService.set_current_user(TEST_USER)

    def test_failed_load_keeps_the_existing_table(self):
        databaseService.runQuery("CREATE TABLE people AS SELECT 1 AS id")
        upload = UploadFile(filename="people.parquet", file=io.BytesIO(b"not parquet"))

        resp = database_controller.uploadFile(file=upload, tableName="people")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(int(databaseService.runQuery("SELECT count(*) AS c FROM people")["c"][0]), 1)

    @staticmethod
    def _bytes(size):
        amount, unit = size.split()
        return float(amount) * databaseService._SIZE_UNITS[unit]

    def test_memory_and_threads_are_limited_per_database(self):
        databaseService._config.update({"duckdbMemoryLimit": "1GB", "duckdbThreads": 2})
        database_controller.changeDatabase("aux")

        row = databaseService.runQuery("SELECT current_setting('memory_limit') AS m, current_setting('threads') AS t")
        self.assertAlmostEqual(self._bytes(row["m"][0]), 10**9, delta=10**7)
        self.assertEqual(int(row["t"][0]), 2)

    def test_with_several_users_the_memory_is_split_among_open_databases(self):
        databaseService._config["duckdbMaxOpenDatabases"] = 4
        database_controller.changeDatabase("aux")

        limit = databaseService.runQuery("SELECT current_setting('memory_limit') AS m")["m"][0]
        with duckdb.connect() as con:
            default = con.execute("SELECT current_setting('memory_limit')").fetchone()[0]
        self.assertAlmostEqual(self._bytes(limit) * 4 / self._bytes(default), 1, delta=0.05)

    def test_idle_databases_are_closed_but_never_while_in_use(self):
        databaseService._config["duckdbIdleMinutes"] = 0
        database_controller.changeDatabase("aux")

        in_use, finished = threading.Event(), threading.Event()

        def request_in_progress():
            with databaseService._user_lock(TEST_USER):
                in_use.set()
                finished.wait()

        request = threading.Thread(target=request_in_progress, daemon=True)
        request.start()
        in_use.wait()
        try:
            databaseService._close_idle_connections()
            self.assertIn("aux.db", databaseService._connections[TEST_USER])
        finally:
            finished.set()
            request.join()

        databaseService._close_idle_connections()
        self.assertNotIn("aux.db", databaseService._connections[TEST_USER])
        # The next request opens it again
        self.assertEqual(int(databaseService.runQuery("SELECT 42 AS n")["n"][0]), 42)
        self.assertIn("aux.db", databaseService._connections[TEST_USER])

    def test_query_result_survives_the_database_being_closed(self):
        databaseService._config["duckdbIdleMinutes"] = 0
        database_controller.changeDatabase("aux")
        databaseService.runQuery("CREATE TABLE numbers AS SELECT range AS n FROM range(5)")
        database_controller.runQuery(QueryRequest(query="SELECT n FROM numbers WHERE n > 2", rows=10))

        databaseService._close_idle_connections()
        self.assertNotIn("aux.db", databaseService._connections[TEST_USER])
        # Reopened, __lastQuery is a view of the same query
        self.assertEqual(databaseService.runQuery("SELECT n FROM __lastQuery ORDER BY n")["n"].to_list(), [3, 4])

    def test_least_recently_used_database_is_closed_beyond_the_limit(self):
        databaseService._config["duckdbMaxOpenDatabases"] = 1
        database_controller.changeDatabase("aux")

        databaseService.set_current_user("other_user")
        try:
            databaseService.runQuery("SELECT 1")
            self.assertNotIn("aux.db", databaseService._connections[TEST_USER])
            self.assertIn("main.db", databaseService._connections["other_user"])
        finally:
            for db in databaseService._connections.pop("other_user", {}).values():
                db.close()
            databaseService._active_db.pop("other_user", None)
            databaseService._last_used.pop(("other_user", "main.db"), None)
            databaseService.set_current_user(TEST_USER)

    def test_upload_file_creates_table(self):
        payload = b"id,name\n1,Ana\n2,Bob\n"
        upload = UploadFile(filename="people.csv", file=io.BytesIO(payload))

        out = database_controller.uploadFile(file=upload, tableName="people")
        self.assertEqual(out["status"], "ok")

        count = databaseService.runQuery("SELECT COUNT(*) AS c FROM people")
        self.assertEqual(int(count["c"].iloc[0]), 2)


if __name__ == '__main__':
    unittest.main()
