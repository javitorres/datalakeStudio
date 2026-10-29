import asyncio
import json
import threading
import unittest
from unittest.mock import patch

import duckdb
import pandas as pd
import pyarrow as pa
from fastapi import HTTPException

from model.QueryRequestDTO import QueryRequest
from routes import database_controller, maps_controller
from services import databaseService, mapsService

TEST_USER = "test_user"


class DatabaseRoutesTest(unittest.TestCase):
    def setUp(self):
        databaseService._config = {"databasesFolder": "/tmp/test_db", "downloadFolder": "/tmp/test_dl"}
        databaseService.set_current_user(TEST_USER)
        db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})
        databaseService._connections[TEST_USER] = {"test.db": db}
        databaseService._active_db[TEST_USER] = "test.db"
        self._seed()

    @staticmethod
    def _csv_lines(response_body: bytes):
        return [line for line in response_body.decode('utf-8').splitlines() if line.strip()]

    def _seed(self):
        databaseService.runQuery(
            """
            CREATE TABLE iris AS
            SELECT * FROM (
                VALUES
                    (1, 'setosa', 5.1),
                    (2, 'versicolor', 6.2),
                    (3, 'virginica', 6.8)
            ) AS t(id, species, sepal_length)
            """
        )

    def test_get_tables_filters_meta_tables(self):
        databaseService.runQuery("CREATE TABLE __lastQuery AS SELECT 1 AS v")
        databaseService.runQuery("CREATE TABLE cube_index_tmp AS SELECT 1 AS v")

        resp = database_controller.getTables()
        self.assertEqual(resp.status_code, 200)
        tables = resp.body.decode('utf-8')

        self.assertIn('iris', tables)
        self.assertNotIn('__lastQuery', tables)
        self.assertNotIn('cube_index_tmp', tables)

    def test_get_database_schema_preserves_order_types_and_filters_meta_tables(self):
        databaseService.runQuery(
            'CREATE TABLE "sales data" ("order total" DECIMAL(10,2), city VARCHAR)'
        )
        databaseService.runQuery('CREATE TABLE __hidden (secret INTEGER)')
        databaseService.runQuery('CREATE TABLE cube_index_hidden (secret INTEGER)')

        resp = database_controller.getDatabaseSchema()
        self.assertEqual(resp.status_code, 200)
        schema = json.loads(resp.body)

        self.assertEqual(list(schema["iris"]), ["id", "species", "sepal_length"])
        self.assertEqual(schema["iris"]["id"], "INTEGER")
        self.assertEqual(schema["iris"]["species"], "VARCHAR")
        self.assertEqual(list(schema["sales data"]), ["order total", "city"])
        self.assertEqual(schema["sales data"]["order total"], "DECIMAL(10,2)")
        self.assertNotIn("__hidden", schema)
        self.assertNotIn("cube_index_hidden", schema)

    def test_map_bbox_and_field_validation(self):
        self.assertEqual(
            maps_controller._parse_bbox("-4,39,-3,41"),
            (39.0, 41.0, -4.0, -3.0)
        )
        with self.assertRaises(HTTPException) as invalid_bbox:
            maps_controller._parse_bbox("not-a-bbox")
        self.assertEqual(invalid_bbox.exception.status_code, 400)

        with self.assertRaises(HTTPException) as unknown_column:
            maps_controller._validated_map_fields("iris", "missing", "sepal_length")
        self.assertEqual(unknown_column.exception.status_code, 400)

        with self.assertRaises(HTTPException) as non_numeric:
            maps_controller._validated_map_fields("iris", "id", "sepal_length", fields=["species"])
        self.assertEqual(non_numeric.exception.status_code, 400)

    def test_map_points_support_special_names_and_no_metrics(self):
        databaseService.runQuery(
            'CREATE TABLE "map data" ("my lat" DOUBLE, "my lon" DOUBLE, label VARCHAR)'
        )
        databaseService.runQuery(
            'INSERT INTO "map data" VALUES (40.4, -3.7, '"'Madrid'"')'
        )

        response = asyncio.run(maps_controller.csv(
            table="map data", latitudeField="my lat", longitudeField="my lon",
            bbox="-4,40,-3,41"
        ))
        body = response.body.decode("utf-8")
        self.assertEqual(response.media_type, "text/csv")
        self.assertEqual(body.splitlines()[0], "latitude,longitude")
        self.assertIn("40.4,-3.7", body)

    def test_h3_query_without_metrics_has_valid_select_list(self):
        with patch.object(databaseService, "runQuery", return_value="result") as run_query:
            result = maps_controller.getH3Data(
                "iris", "id", "sepal_length", [], level=5,
                lat_min=-90, lat_max=90, lon_min=-180, lon_max=180
            )

        self.assertEqual(result, "result")
        sql = run_query.call_args.args[0]
        self.assertIn("count(*) AS count", sql)
        self.assertNotIn("count(*) AS count, FROM", " ".join(sql.split()))
        self.assertIn('FROM "iris"', sql)

    def test_geometry_query_keeps_lon_lat_order_and_intersects_bbox(self):
        with patch.object(databaseService, "runQuery", return_value="result") as run_query:
            maps_controller.getGeom("parcels", "geom")

        sql = run_query.call_args.args[0]
        self.assertEqual(sql.count("always_xy := true"), 2)
        self.assertIn("ST_Intersects(", sql)
        self.assertNotIn("ST_Within(", sql)

    def test_geometry_layer_returns_features_inside_bbox(self):
        try:
            databaseService.runQuery("INSTALL spatial; LOAD spatial;", False)
        except Exception:
            self.skipTest("spatial extension not available")
        databaseService.runQuery("CREATE TABLE parcels AS SELECT 'POINT (440291 4474254)' AS geom, 'Madrid' AS name")

        df = maps_controller.getGeom("parcels", "geom", lat_min=40, lat_max=41, lon_min=-4, lon_max=-3)
        self.assertEqual(df["name"].to_list(), ["Madrid"])
        self.assertTrue(df["geom"][0].startswith("POINT (-3.70"))

    def test_s3_credentials_are_stored_as_a_secret(self):
        previous_secrets = databaseService._secrets
        databaseService._secrets = {"s3_access_key_id": "AKIAEXAMPLE", "s3_secret_access_key": "dummy"}
        db = duckdb.connect(':memory:')
        try:
            databaseService._load_extensions_for_db(db)
            secrets = db.query("SELECT name FROM duckdb_secrets()").fetchall()
            if ("datalake_s3",) not in secrets:
                self.skipTest("httpfs extension not available")
            used = db.query("SELECT name FROM which_secret('s3://bucket/data.parquet', 's3')").fetchall()
            self.assertEqual(used, [("datalake_s3",)])
        finally:
            databaseService._secrets = previous_secrets
            db.close()

    def test_mapbox_token_reports_missing_configuration(self):
        previous_token = mapsService.mapbox_access_token
        mapsService.mapbox_access_token = None
        try:
            with self.assertRaises(HTTPException) as unavailable:
                maps_controller.getMapboxToken()
            self.assertEqual(unavailable.exception.status_code, 503)
        finally:
            mapsService.mapbox_access_token = previous_token

    def test_get_table_schema(self):
        resp = database_controller.getTableSchema('iris')
        self.assertEqual(resp.status_code, 200)
        body = resp.body.decode('utf-8')

        self.assertIn('id', body)
        self.assertIn('species', body)
        self.assertIn('sepal_length', body)

    def test_get_sample_data_with_limit(self):
        resp = database_controller.getTableData('iris', records=2)
        self.assertEqual(resp.status_code, 200)
        lines = self._csv_lines(resp.body)

        # header + 2 rows
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'id,species,sepal_length')

    def test_sample_first_last_and_random_rows(self):
        def ids(**kwargs):
            resp = database_controller.getTableData('iris', **kwargs)
            return [line.split(',')[0] for line in self._csv_lines(resp.body)[1:]]

        self.assertEqual(ids(type='First', records=2), ['1', '2'])
        self.assertEqual(ids(type='Last', records=2), ['2', '3'])
        self.assertEqual(ids(type='Last', records=1, filter='id < 3'), ['2'])
        # Random rows are drawn from the filtered ones
        self.assertEqual(sorted(ids(type='Shuffle', records=2, filter='id > 1')), ['2', '3'])

    def test_run_query_success_and_invalid_query(self):
        ok = database_controller.runQuery(QueryRequest(query='SELECT id, species FROM iris ORDER BY id', rows=2))
        self.assertEqual(ok.status_code, 200)
        ok_lines = self._csv_lines(ok.body)
        self.assertEqual(ok_lines[0], 'id,species')
        self.assertEqual(len(ok_lines), 3)

        bad = database_controller.runQuery(QueryRequest(query='SELECT * FROM does_not_exist', rows=2))
        self.assertEqual(bad.status_code, 400)
        self.assertIn('Error running query', bad.body.decode('utf-8'))

    def test_run_query_scripts_comments_and_other_statements(self):
        def run(sql):
            resp = database_controller.runQuery(QueryRequest(query=sql, rows=10))
            body = self._csv_lines(resp.body) if resp.status_code == 200 else json.loads(resp.body)["message"]
            return resp.status_code, body

        self.assertEqual(run("SELECT 42 AS answer -- trailing comment"), (200, ["answer", "42"]))
        status, message = run("   -- nothing to run")
        self.assertEqual(status, 400)
        self.assertIn("empty", message)
        # In a script the earlier statements run and the last one gives the result
        self.assertEqual(run("CREATE TABLE setosa AS FROM iris WHERE species = 'setosa'; SELECT count(*) AS n FROM setosa;"),
                         (200, ["n", "1"]))
        # Statements that aren't queries run once and keep what they return
        self.assertEqual(run("INSERT INTO iris VALUES (4, 'new', 7.0) RETURNING id"), (200, ["id", "4"]))
        self.assertEqual(int(databaseService.runQuery("SELECT count(*) AS n FROM iris")["n"][0]), 4)
        self.assertEqual(run("EXPLAIN SELECT 1")[0], 200)
        self.assertEqual(list(databaseService.runQuery("SELECT * FROM __lastQuery").columns), ["explain_key", "explain_value"])
        # DuckDB 1.5 can't wrap these in CREATE TABLE AS, and splits PIVOT in two
        self.assertEqual(run("SUMMARIZE iris")[0], 200)
        self.assertEqual(run("PIVOT (SELECT species FROM iris) ON species USING count(*)")[1],
                         ["new,setosa,versicolor,virginica", "1,1,1,1"])
        status, message = run("SELECT * FROM does_not_exist")
        self.assertEqual(status, 400)
        self.assertIn("does_not_exist", message)

    def test_query_results_are_not_written_to_the_database_file(self):
        databaseService.runQuery("CREATE TABLE __lastQuery AS SELECT 1 AS old")  # as earlier versions left it
        database_controller.runQuery(QueryRequest(query="SELECT * FROM iris", rows=10))

        catalogs = databaseService.runQuery(
            "SELECT DISTINCT table_catalog AS c FROM information_schema.tables WHERE starts_with(table_name, '__lastQuery')")
        self.assertEqual(catalogs["c"].to_list(), ["temp"])
        self.assertEqual(int(databaseService.runQuery("SELECT count(*) AS n FROM __lastQuery")["n"][0]), 3)

    def test_map_of_a_query_result(self):
        databaseService.runQuery("CREATE TABLE places AS SELECT 40.4 AS lat, -3.7 AS lon")
        database_controller.runQuery(QueryRequest(query="SELECT * FROM places", rows=10))

        response = asyncio.run(maps_controller.csv(table="__lastQuery", latitudeField="lat", longitudeField="lon",
                                                   bbox="-4,40,-3,41"))
        self.assertIn("40.4,-3.7", response.body.decode("utf-8"))

    def test_create_rowcount_and_delete_table(self):
        created = database_controller.createTableFromQuery('SELECT * FROM iris', 'iris_copy')
        self.assertEqual(created['status'], 'ok')

        rowcount = database_controller.getRowsCount('iris_copy')
        self.assertEqual(rowcount['status'], 'ok')
        self.assertEqual(rowcount['rows'], '3')

        deleted = database_controller.deleteTable('iris_copy')
        self.assertEqual(deleted['status'], 'ok')

        tables_resp = database_controller.getTables()
        tables = tables_resp.body.decode('utf-8')
        self.assertNotIn('iris_copy', tables)

    def test_failed_create_table_from_query_keeps_the_table(self):
        resp = database_controller.createTableFromQuery('SELECT * FROM does_not_exist', 'iris')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(int(databaseService.runQuery("SELECT count(*) AS n FROM iris")["n"][0]), 3)

        # The query can read the table it replaces
        out = database_controller.createTableFromQuery("SELECT * FROM iris WHERE species <> 'setosa'", 'iris')
        self.assertEqual(out["status"], "ok")
        self.assertEqual(int(databaseService.runQuery("SELECT count(*) AS n FROM iris")["n"][0]), 2)

    def test_concurrent_requests_share_the_user_connection(self):
        databaseService.runQuery("CREATE TABLE big AS SELECT range AS i FROM range(3000000)")
        errors = []

        def request_thread():
            databaseService.set_current_user(TEST_USER)
            try:
                for _ in range(5):
                    databaseService.runQuery("SELECT sum(i) AS s FROM big", False)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=request_thread) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])

    def test_rest_connector_arrow_returns_ipc_stream(self):
        class ArrowRequest:
            async def json(self):
                return {"type": "arrow", "sql": "SELECT id, species FROM iris ORDER BY id"}

        resp = asyncio.run(database_controller.handle_query(ArrowRequest()))
        table = pa.ipc.open_stream(resp.body).read_all()
        self.assertEqual(table.column_names, ["id", "species"])
        self.assertEqual(table.num_rows, 3)

    def test_rest_connector_json_handles_nulls_and_dates(self):
        class JsonRequest:
            async def json(self):
                return {"type": "json", "sql": "SELECT NULL::DOUBLE AS price, DATE '2026-01-02' AS d"}

        resp = asyncio.run(database_controller.handle_query(JsonRequest()))
        self.assertEqual(json.loads(resp.body), [{"price": None, "d": "2026-01-02T00:00:00.000"}])

    def test_create_table_from_dataframe(self):
        df = pd.DataFrame({"id": [1, 2], "city": ["Madrid", "Sevilla"]})
        databaseService.createTableFromDataFrame(df, "imported")

        rows = databaseService.runQuery("SELECT * FROM imported ORDER BY id")
        self.assertEqual(rows["city"].to_list(), ["Madrid", "Sevilla"])
        self.assertNotIn("__dataframe_import", databaseService.getTableList(hideMeta=False))


if __name__ == '__main__':
    unittest.main()
