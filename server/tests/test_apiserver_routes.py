import base64
import json
import unittest

import duckdb

from routes import apiserver_controller
from services import apiServerService, databaseService

TEST_USER = "test_user"


class ApiServerRoutesTest(unittest.TestCase):
    def setUp(self):
        databaseService._config = {"databasesFolder": "/tmp/test_db", "downloadFolder": "/tmp/test_dl"}
        databaseService.set_current_user(TEST_USER)
        db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})
        databaseService._connections[TEST_USER] = {"test.db": db}
        databaseService._active_db[TEST_USER] = "test.db"
        apiServerService.createTable()

    @staticmethod
    def _json(response):
        return json.loads(response.body.decode('utf-8'))

    def test_list_endpoints_empty(self):
        resp = apiserver_controller.listEndpoints()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), [])

    def test_create_get_delete_endpoint(self):
        create_resp = apiserver_controller.create()
        self.assertEqual(create_resp.status_code, 200)
        endpoint_id = self._json(create_resp)['id_endpoint']
        self.assertIsInstance(endpoint_id, int)

        get_resp = apiserver_controller.getEndpoint(endpoint_id)
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(self._json(get_resp)['id_endpoint'], endpoint_id)

        delete_resp = apiserver_controller.deleteEndpoint(endpoint_id)
        self.assertEqual(delete_resp.status_code, 200)

        missing_resp = apiserver_controller.getEndpoint(endpoint_id)
        self.assertEqual(missing_resp.status_code, 404)

    def test_update_endpoint_persists_fields(self):
        create_resp = apiserver_controller.create()
        endpoint_id = self._json(create_resp)['id_endpoint']

        payload = {
            'id_query': 7,
            'id_endpoint': endpoint_id,
            'endpoint': 'carsByBrand',
            'parameters': [{'name': 'brand', 'exampleValue': 'FORD'}],
            'description': 'Search cars by brand',
            'query': base64.b64encode('SELECT 1 AS one'.encode('utf-8')).decode('utf-8'),
            'queryStringTest': '?brand=FORD',
            'status': 'DEV',
        }

        dto = apiserver_controller.PublishEndpointRequestDTO(**payload)
        update_resp = apiserver_controller.publish(dto)
        self.assertEqual(update_resp.status_code, 200)

        get_resp = apiserver_controller.getEndpoint(endpoint_id)
        self.assertEqual(get_resp.status_code, 200)
        body = self._json(get_resp)

        self.assertEqual(body['id_query'], 7)
        self.assertEqual(body['endpoint'], 'carsByBrand')
        self.assertEqual(body['description'], 'Search cars by brand')
        self.assertEqual(body['query'], 'SELECT 1 AS one')
        self.assertEqual(body['queryStringTest'], '?brand=FORD')
        self.assertEqual(body['status'], 'DEV')
        self.assertIn('brand', body['parameters'])

    @staticmethod
    def _publish(endpoint, query):
        databaseService.runQuery(
            "INSERT INTO __endpoints VALUES (nextval('seq_id_endpoint'), 1, ?, '[]', '', ?, '', 'DEV')",
            params=[endpoint, query])

    def test_endpoint_parameters_are_bound_not_pasted(self):
        databaseService.runQuery(
            "CREATE TABLE iris AS SELECT * FROM (VALUES (5.0, 'setosa'), (6.5, 'virginica')) t(sepal_length, species)")
        self._publish("irisBySize",
                      "SELECT species FROM iris WHERE sepal_length >= {min_length} AND species LIKE '%{name}%' ORDER BY species")

        df = apiServerService.getAndRunEndpoint("irisBySize", {"min_length": "5", "name": "a"}, None)
        self.assertEqual(df["species"].to_list(), ["setosa", "virginica"])

        with self.assertRaises(Exception):
            apiServerService.getAndRunEndpoint(
                "irisBySize", {"min_length": "0; CREATE TABLE pwned AS SELECT 1", "name": "a"}, None)
        self.assertNotIn("pwned", databaseService.getTableList())

        df = apiServerService.getAndRunEndpoint("irisBySize", {"min_length": "0", "name": "x' OR '1'='1"}, None)
        self.assertEqual(len(df), 0)

    def test_quoted_placeholder_still_matches_numeric_columns(self):
        databaseService.runQuery("CREATE TABLE cars AS SELECT * FROM (VALUES (1, 'FORD'), (2, 'SEAT')) t(id, brand)")
        self._publish("carById", "SELECT brand FROM cars WHERE id = '{id}'")

        df = apiServerService.getAndRunEndpoint("carById", {"id": "2"}, None)
        self.assertEqual(df["brand"].to_list(), ["SEAT"])

    def test_missing_parameters_are_reported_without_the_sql(self):
        self._publish("needsParams", "SELECT {a} AS a, {b} AS b, {b} AS b2")

        with self.assertRaises(ValueError) as error:
            apiServerService.getAndRunEndpoint("needsParams", {"a": "1"}, None)
        self.assertEqual(str(error.exception), "Missing parameters: b")

    def test_comments_and_struct_literals_are_not_placeholders(self):
        self._publish("structs", "SELECT {'k': 1} AS s -- {not_a_param}\n, {v} AS v")

        df = apiServerService.getAndRunEndpoint("structs", {"v": "x"}, None)
        self.assertEqual(df["v"].to_list(), ["x"])

    def test_endpoint_lookup_does_not_parse_the_path(self):
        self._publish("real", "SELECT 1 AS one")

        self.assertIsNone(apiServerService.getEndpointConfiguration("x' OR '1'='1"))
        self.assertIsNotNone(apiServerService.getEndpointConfiguration("real"))


if __name__ == '__main__':
    unittest.main()
