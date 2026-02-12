import json
import unittest
from unittest.mock import patch

import pandas as pd

from routes import remoteDb_controller


class _FakeConfig:
    def __init__(self):
        self.get_secrets = {'pgpass_file': '/tmp/pgpass'}


class RemoteDbControllerTest(unittest.TestCase):
    def setUp(self):
        if hasattr(remoteDb_controller, 'connection'):
            remoteDb_controller.connection = None

    @staticmethod
    def _json(response):
        return json.loads(response.body.decode('utf-8'))

    @patch('routes.remoteDb_controller.Config.get_instance', return_value=_FakeConfig())
    @patch('routes.remoteDb_controller.remoteDbService.getDbList')
    def test_get_database_list(self, mock_get_list, _mock_cfg):
        mock_get_list.return_value = ['host - 5432 - db - user']

        resp = remoteDb_controller.getDatabaseList('db')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), ['host - 5432 - db - user'])

    @patch('routes.remoteDb_controller.Config.get_instance', return_value=_FakeConfig())
    @patch('routes.remoteDb_controller.remoteDbService.getSchemas')
    @patch('routes.remoteDb_controller.remoteDbService.connectDatabase')
    def test_connect_database_success(self, mock_connect, mock_get_schemas, _mock_cfg):
        mock_connect.return_value = object()
        mock_get_schemas.return_value = ['public']

        resp = remoteDb_controller.connectDatabase('host - 5432 - db - user')
        self.assertEqual(resp.status_code, 200)
        body = self._json(resp)
        self.assertEqual(body['status'], 'ok')
        self.assertEqual(body['schemas'], ['public'])

    @patch('routes.remoteDb_controller.Config.get_instance', return_value=_FakeConfig())
    @patch('routes.remoteDb_controller.remoteDbService.connectDatabase')
    def test_connect_database_error_status(self, mock_connect, _mock_cfg):
        mock_connect.return_value = None

        resp = remoteDb_controller.connectDatabase('x')
        self.assertEqual(resp, {'status': 'error'})

    def test_get_schemas_requires_connection(self):
        remoteDb_controller.connection = None
        resp = remoteDb_controller.getSchemas()
        self.assertEqual(resp.status_code, 400)

    @patch('routes.remoteDb_controller.remoteDbService.getSchemas', return_value=['public'])
    def test_get_schemas_ok(self, _mock):
        remoteDb_controller.connection = object()
        resp = remoteDb_controller.getSchemas()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), ['public'])

    def test_run_remote_query_requires_connection(self):
        remoteDb_controller.connection = None
        resp = remoteDb_controller.runRemoteQuery('select 1')
        self.assertEqual(resp.status_code, 400)

    @patch('routes.remoteDb_controller.remoteDbService.runRemoteQuery')
    def test_run_remote_query_ok(self, mock_run):
        remoteDb_controller.connection = object()
        mock_run.return_value = pd.DataFrame([{'id': 1}])

        resp = remoteDb_controller.runRemoteQuery('select 1 as id')
        self.assertEqual(resp.status_code, 200)
        body = self._json(resp)
        self.assertIn('id', body)

    @patch('routes.remoteDb_controller.databaseService.createTableFromDataFrame')
    @patch('routes.remoteDb_controller.remoteDbService.runRemoteQuery')
    def test_create_table_from_remote_query_ok(self, mock_run, mock_create):
        remoteDb_controller.connection = object()
        mock_run.return_value = pd.DataFrame([{'id': 1}])

        resp = remoteDb_controller.createTableFromRemoteQuery('select 1 as id', 'new_table')
        self.assertEqual(resp, {'status': 'ok'})
        mock_create.assert_called_once_with('dfRemoteDb', 'new_table')


if __name__ == '__main__':
    unittest.main()
