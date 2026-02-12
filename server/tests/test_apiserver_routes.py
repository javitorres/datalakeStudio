import base64
import json
import unittest

import duckdb

from routes import apiserver_controller
from services import apiServerService, databaseService


class ApiServerRoutesTest(unittest.TestCase):
    def setUp(self):
        databaseService.db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})
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


if __name__ == '__main__':
    unittest.main()
