import asyncio
import json
import unittest
from unittest.mock import patch

import duckdb
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

    def test_run_query_success_and_invalid_query(self):
        ok = database_controller.runQuery(QueryRequest(query='SELECT id, species FROM iris ORDER BY id', rows=2))
        self.assertEqual(ok.status_code, 200)
        ok_lines = self._csv_lines(ok.body)
        self.assertEqual(ok_lines[0], 'id,species')
        self.assertEqual(len(ok_lines), 3)

        bad = database_controller.runQuery(QueryRequest(query='SELECT * FROM does_not_exist', rows=2))
        self.assertEqual(bad.status_code, 400)
        self.assertIn('Error running query', bad.body.decode('utf-8'))

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


if __name__ == '__main__':
    unittest.main()
