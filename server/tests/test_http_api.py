"""HTTP tests of the whole app (server.py) with login on, in a temporary folder.

DuckDB extensions are not downloaded, so the tests run offline; the map and S3 paths that need
extensions are covered by the tests that load them when they are available.
"""
import asyncio
import base64
import io
import os
import tempfile
import unittest

import duckdb
import httpx
import pyarrow as pa

from config import Config
from services import authService, databaseService, mailService

ALICE, BOB = "alice@example.com", "bob@example.com"
CSV = "city,price\nMadrid,350000\nSevilla,210000\nBilbao,280000\nMadrid,410000\n"


class HttpApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.previous_config = Config._instance
        config = Config.__new__(Config)
        config.config = {"databasesFolder": os.path.join(cls.tmp.name, "data"),
                         "downloadFolder": os.path.join(cls.tmp.name, "temp"),
                         "defaultDatabase": "datalakeStudio.db", "authEnabled": True,
                         "allowedOrigins": ["http://localhost:8080"]}
        config.secrets = {"jwt_secret": "http-test-secret-" + "x" * 32}
        Config._instance = config
        databaseService.init(config.secrets, config.config)
        mailService.init(config.secrets)
        authService.init(config.config, config.secrets)
        cls.load_extensions = databaseService._load_extensions_for_db
        databaseService._load_extensions_for_db = lambda db: None

        import server
        cls.app = server.app
        cls.alice = cls._request("POST", "/auth/register", json={"username": ALICE, "password": "secret1"}).json()["token"]
        cls.bob = cls._request("POST", "/auth/register", json={"username": BOB, "password": "secret1"}).json()["token"]

    @classmethod
    def tearDownClass(cls):
        databaseService._load_extensions_for_db = cls.load_extensions
        for user in (ALICE, BOB):
            for db_name, db in databaseService._connections.pop(user, {}).items():
                db.close()
                databaseService._last_used.pop((user, db_name), None)
            databaseService._active_db.pop(user, None)
        Config._instance = cls.previous_config
        cls.tmp.cleanup()

    @classmethod
    def _request(cls, method, path, token=None, **kwargs):
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        async def call():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=cls.app), base_url="http://test") as client:
                return await client.request(method, path, headers=headers, **kwargs)

        return asyncio.run(call())

    def _upload(self, token, table, content=CSV, file_name="data.csv"):
        return self._request("POST", "/database/uploadFile", token,
                             files={"file": (file_name, content)}, data={"tableName": table})

    def _exec(self, token, sql):
        return self._request("POST", "/database/restConnector", token, json={"type": "exec", "sql": sql})

    def test_requests_need_a_valid_token(self):
        self.assertEqual(self._request("GET", "/database/getTables").status_code, 401)
        self.assertEqual(self._request("GET", "/database/getTables", "not-a-token").status_code, 401)

    def test_load_query_and_export_a_table(self):
        self.assertEqual(self._upload(self.alice, "places").json()["status"], "ok")
        self.assertIn("places", self._request("GET", "/database/getTables", self.alice).json())

        sample = self._request("GET", "/database/getSampleData", self.alice, params={"tableName": "places", "records": 2})
        self.assertEqual(sample.text.splitlines(), ["city,price", "Madrid,350000", "Sevilla,210000"])
        query = {"query": "SELECT city, count(*) AS n FROM places GROUP BY ALL ORDER BY n DESC, city", "rows": 10}
        self.assertEqual(self._request("POST", "/database/runQuery", self.alice, json=query).text.splitlines()[1], "Madrid,2")
        average = self._request("POST", "/database/restConnector", self.alice,
                                json={"type": "json", "sql": "SELECT avg(price) AS avg_price FROM places"})
        self.assertEqual(average.json(), [{"avg_price": 312500.0}])
        arrow = self._request("POST", "/database/restConnector", self.alice, json={"type": "arrow", "sql": "SELECT * FROM places"})
        self.assertEqual(pa.ipc.open_stream(io.BytesIO(arrow.content)).read_all().num_rows, 4)
        export = self._request("GET", "/database/exportData", self.alice, params={"tableName": "places", "format": "parquet"})
        self.assertEqual(export.content[:4], b"PAR1")

        broken = self._upload(self.alice, "broken", b"not parquet", "broken.parquet")
        self.assertEqual(broken.status_code, 400)
        self.assertIn("parquet", broken.json()["message"].lower())
        missing = self._request("GET", "/database/getSampleData", self.alice, params={"tableName": "does_not_exist"})
        self.assertEqual(missing.status_code, 500)
        self.assertIn("does_not_exist", missing.json()["message"])

    def test_published_endpoint_binds_its_parameters(self):
        self._upload(self.alice, "prices")
        endpoint_id = self._request("GET", "/apiserver/create", self.alice).json()["id_endpoint"]
        query = "SELECT city FROM prices WHERE price >= {min} AND city LIKE '%{name}%' ORDER BY price"
        update = self._request("POST", "/apiserver/update", self.alice, json={
            "id_query": 1, "id_endpoint": endpoint_id, "endpoint": "byMinPrice",
            "parameters": [{"name": "min", "exampleValue": "300000"}, {"name": "name", "exampleValue": "a"}],
            "description": "", "query": base64.b64encode(query.encode()).decode(),
            "queryStringTest": "?min=300000&name=a", "status": "DEV"})
        self.assertEqual(update.status_code, 200)

        api = lambda path, **params: self._request("GET", path, self.alice, params=params)
        self.assertEqual(api("/api/byMinPrice", min="300000", name="a").json(), [{"city": "Madrid"}, {"city": "Madrid"}])
        self.assertEqual(api("/api/byMinPrice", min="0; CREATE TABLE pwned AS SELECT 1", name="a").status_code, 400)
        self.assertNotIn("pwned", self._request("GET", "/database/getTables", self.alice).json())
        self.assertEqual(api("/api/byMinPrice", min="0", name="x' OR '1'='1").json(), [])
        self.assertEqual(api("/api/x' OR '1'='1").status_code, 404)
        self.assertIn("/byMinPrice", api("/api/").json()["paths"])

    def test_users_cannot_reach_each_other(self):
        self._upload(self.bob, "bob_places")
        bob_db = os.path.join(self.tmp.name, "data", BOB, "datalakeStudio.db")
        bob_db_size = os.path.getsize(bob_db)
        # A database the server doesn't have open (an open one is refused for another reason)
        carol_db = os.path.join(self.tmp.name, "data", "carol@example.com", "datalakeStudio.db")
        os.makedirs(os.path.dirname(carol_db))
        duckdb.connect(carol_db).close()
        outside = os.path.join(self.tmp.name, "outside.csv")
        with open(outside, "w", encoding="utf-8") as f:
            f.write("a\n1\n")

        register = self._request("POST", "/auth/register", json={"username": BOB + "/.", "password": "secret1"})
        self.assertEqual(register.status_code, 409)
        change = self._request("GET", "/database/changeDatabase", self.alice, params={"databaseName": "../" + BOB + "/datalakeStudio"})
        self.assertEqual(change.status_code, 400)
        for sql in (f"ATTACH '{carol_db}' AS c", f"SELECT * FROM read_csv('{outside}')",
                    f"COPY (SELECT 1) TO '{os.path.join(self.tmp.name, 'written.csv')}'", "SET enable_external_access = true"):
            self.assertEqual(self._exec(self.alice, sql).status_code, 500, sql)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "written.csv")))
        load = self._request("GET", "/database/loadFile", self.alice, params={"fileName": bob_db, "tableName": "stolen"})
        self.assertEqual(load.status_code, 400)
        self._upload(self.alice, "x", b"garbage", "../../data/" + BOB + "/datalakeStudio.db")

        self.assertEqual(os.path.getsize(bob_db), bob_db_size)
        self.assertEqual(self._request("GET", "/database/getTables", self.bob).json(), ["bob_places"])

    def test_concurrent_requests_from_two_users(self):
        async def burst():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as client:
                requests = []
                for i in range(48):
                    token = self.alice if i % 2 else self.bob
                    sql = "SELECT count(*) AS n FROM range(2000000)" if i % 3 else "SELECT 1 AS n"
                    requests.append(client.post("/database/restConnector", json={"type": "json", "sql": sql},
                                                headers={"Authorization": f"Bearer {token}"}))
                return await asyncio.gather(*requests)

        codes = [response.status_code for response in asyncio.run(burst())]
        self.assertEqual(codes.count(200), 48)

    def test_databases_beyond_the_limit_are_closed_and_reopened(self):
        self._request("GET", "/database/getTables", self.alice)
        databaseService._config["duckdbMaxOpenDatabases"] = 1
        try:
            # Opening another database (bob switches to a new one) closes the least recently used
            switch = self._request("GET", "/database/changeDatabase", self.bob, params={"databaseName": "second"})
            self.assertEqual(switch.status_code, 200)
            self.assertNotIn("datalakeStudio.db", databaseService._connections[ALICE])
            # and alice's next request opens hers again
            self.assertEqual(self._request("GET", "/database/getTables", self.alice).status_code, 200)
            self.assertIn("datalakeStudio.db", databaseService._connections[ALICE])
        finally:
            del databaseService._config["duckdbMaxOpenDatabases"]
            self._request("GET", "/database/changeDatabase", self.bob, params={"databaseName": "datalakeStudio"})


    DASHBOARD = {
        "title": "Homes", "history": [{"role": "user", "text": "homes by city"}],
        "spec": {
            "title": "Homes",
            "datasets": [{"id": "homes", "sql": "SELECT * FROM homes", "columns": {"city": "VARCHAR", "price": "BIGINT"}}],
            "filters": [{"id": "f1", "column": "city", "type": "select", "label": "City"},
                        {"id": "f2", "column": "price", "type": "range", "label": "Price"}],
            "widgets": [{"id": "w1", "type": "bar", "title": "Homes by city", "dataset": "homes", "dimension": "city",
                         "measures": [{"column": "*", "agg": "count", "label": "Homes"}]}],
        },
    }
    WIDGET_SQL = ("WITH d AS (SELECT * FROM (SELECT * FROM homes) AS s WHERE "
                  "({f2_min}::DOUBLE IS NULL OR \"price\" >= {f2_min}::DOUBLE) AND "
                  "({f2_max}::DOUBLE IS NULL OR \"price\" <= {f2_max}::DOUBLE)) "
                  "SELECT CAST(\"city\" AS VARCHAR) AS x, count(*) AS m0 FROM d GROUP BY \"city\" ORDER BY m0 DESC, x")
    FILTER_SQL = ("SELECT CAST(\"city\" AS VARCHAR) AS value, count(*) AS n FROM (SELECT * FROM homes) AS s "
                  "WHERE ({f1}::VARCHAR[] IS NULL OR CAST(\"city\" AS VARCHAR) IN (SELECT unnest({f1}::VARCHAR[]))) "
                  "GROUP BY 1 ORDER BY 1")

    def _publish(self, token, dashboard_id, path, queries=None):
        return self._request("PUT", f"/dashboards/{dashboard_id}/publish", token,
                             json={"path": path, "queries": queries or {"w1": self.WIDGET_SQL, "f1": self.FILTER_SQL}})

    def test_dashboards_are_saved_per_user(self):
        saved = self._request("PUT", "/dashboards/dash-private1", self.alice, json=self.DASHBOARD).json()
        self.assertEqual((saved["title"], saved["database"], saved["published"]), ("Homes", "datalakeStudio", None))
        self.assertNotIn("spec", saved)

        self.assertIn("dash-private1", [d["id"] for d in self._request("GET", "/dashboards", self.alice).json()])
        self.assertEqual(self._request("GET", "/dashboards/dash-private1", self.alice).json()["spec"], self.DASHBOARD["spec"])
        self.assertEqual(self._request("GET", "/dashboards", self.bob).json(), [])
        self.assertEqual(self._request("GET", "/dashboards/dash-private1", self.bob).status_code, 404)
        self.assertEqual(self._request("GET", "/dashboards/users.json", self.alice).status_code, 400)
        self.assertEqual(self._request("GET", "/dashboards").status_code, 401)

        self.assertEqual(self._request("DELETE", "/dashboards/dash-private1", self.alice).json(), {"status": "ok"})
        self.assertEqual(self._request("DELETE", "/dashboards/dash-private1", self.alice).status_code, 404)

    def test_published_dashboard_runs_on_its_authors_database(self):
        self._upload(self.alice, "homes")
        self._request("PUT", "/dashboards/dash-homes01", self.alice, json=self.DASHBOARD)
        published = self._publish(self.alice, "dash-homes01", "Homes/By_City/")
        self.assertEqual(published.json()["published"]["path"], "homes/by_city")

        # Another user opens it: the specification without its SQL, and the data of the author
        self.assertEqual(self._request("GET", "/d/homes/by_city").status_code, 401)
        listed = self._request("GET", "/d", self.bob).json()
        self.assertEqual([(d["path"], d["owner"]) for d in listed], [("homes/by_city", ALICE)])
        opened = self._request("GET", "/d/homes/by_city", self.bob).json()
        self.assertEqual((opened["title"], opened["owner"]), ("Homes", ALICE))
        self.assertEqual(opened["spec"]["widgets"], self.DASHBOARD["spec"]["widgets"])
        self.assertNotIn("sql", opened["spec"]["datasets"][0])
        self.assertNotIn("queries", opened)

        def rows(query, filters=None):
            return self._request("POST", "/d/homes/by_city", self.bob, json={"query": query, "filters": filters or {}})

        self.assertEqual(rows("w1").json(), [{"x": "Madrid", "m0": 2}, {"x": "Bilbao", "m0": 1}, {"x": "Sevilla", "m0": 1}])
        self.assertEqual(rows("w1", {"f2": [300000, None]}).json(), [{"x": "Madrid", "m0": 2}])
        self.assertEqual(rows("f1", {"f1": ["Bilbao", "Sevilla"]}).json(),
                         [{"value": "Bilbao", "n": 1}, {"value": "Sevilla", "n": 1}])
        # The values of the viewer are parameters, never SQL
        self.assertEqual(rows("f1", {"f1": ["x')) OR true --"]}).json(), [])
        self.assertEqual(rows("w1", {"f2": ["0 OR 1=1", "1; DROP TABLE homes"]}).json()[0], {"x": "Madrid", "m0": 2})
        self.assertEqual(rows("w9").status_code, 404)
        self.assertEqual(self._request("POST", "/d/homes/other", self.bob, json={"query": "w1"}).status_code, 404)
        # Bob has no table homes of his own, and can't change or unpublish it
        self.assertEqual(self._request("DELETE", "/dashboards/dash-homes01/publish", self.bob).status_code, 404)
        self._request("PUT", "/dashboards/dash-bobs001", self.bob, json=self.DASHBOARD)
        self.assertEqual(self._publish(self.bob, "dash-bobs001", "homes/by_city").status_code, 400)
        self.assertEqual(self._publish(self.bob, "dash-bobs001", "homes/by_city", {"w1": "SELECT 1 AS x"}).status_code, 409)

        # Publishing again under another path moves it; unpublishing removes it
        self.assertEqual(self._publish(self.alice, "dash-homes01", "homes").status_code, 200)
        self.assertEqual(self._request("GET", "/d/homes/by_city", self.bob).status_code, 404)
        self.assertEqual(rows("w1").status_code, 404)
        unpublished = self._request("DELETE", "/dashboards/dash-homes01/publish", self.alice).json()
        self.assertIsNone(unpublished["published"])
        self.assertEqual(self._request("GET", "/d", self.bob).json(), [])

    def test_only_single_selects_and_valid_paths_are_published(self):
        self._upload(self.alice, "homes")
        self._request("PUT", "/dashboards/dash-checks1", self.alice, json=self.DASHBOARD)

        for sql in ("DROP TABLE homes", "SELECT 1; DROP TABLE homes", "COPY homes TO 'homes.csv'",
                    "SELECT * FROM no_such_table", "SELECT {unknown}"):
            response = self._publish(self.alice, "dash-checks1", "checks", {"w1": sql})
            self.assertEqual(response.status_code, 400, sql)
        self.assertEqual(self._publish(self.alice, "dash-checks1", "checks", {"w7": "SELECT 1"}).status_code, 400)
        for path in ("../users", "a/../b", "a b", "a/b/c/d/e/f", ".published/x", "/"):
            self.assertEqual(self._publish(self.alice, "dash-checks1", path).status_code, 400, path)
        self.assertEqual(self._request("GET", "/d", self.bob).json(), [])
        self.assertEqual(self._exec(self.alice, "SELECT count(*) FROM homes").status_code, 200)

    def test_deleting_a_dashboard_unpublishes_it(self):
        self._upload(self.alice, "homes")
        self._request("PUT", "/dashboards/dash-delete1", self.alice, json=self.DASHBOARD)
        self._publish(self.alice, "dash-delete1", "to-delete")
        self.assertEqual(self._request("GET", "/d/to-delete", self.bob).status_code, 200)

        self._request("DELETE", "/dashboards/dash-delete1", self.alice)

        self.assertEqual(self._request("GET", "/d/to-delete", self.bob).status_code, 404)


if __name__ == '__main__':
    unittest.main()
