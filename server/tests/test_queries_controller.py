import json
import unittest
from unittest.mock import patch

import duckdb
import pandas as pd

from model.SaveQueryRequestDTO import SaveQueryRequestDTO
from routes import queries_controller
from services import databaseService, queriesService

TEST_USER = "test_user"


class QueriesControllerTest(unittest.TestCase):
    @staticmethod
    def _json(response):
        return json.loads(response.body.decode('utf-8'))

    def test_save_and_search_queries_with_quotes(self):
        databaseService._config = {"databasesFolder": "/tmp/test_db", "downloadFolder": "/tmp/test_dl"}
        databaseService.set_current_user(TEST_USER)
        databaseService._connections[TEST_USER] = {"test.db": duckdb.connect(':memory:')}
        databaseService._active_db[TEST_USER] = "test.db"

        queriesService.saveSqlQuery(SaveQueryRequestDTO(
            query="SELECT * FROM t WHERE country = 'Andorra'", sqlQueryName="Ventas d'Andorra", description="it's a test"))

        found = queriesService.searchQuery("d'andorra").to_dict(orient="records")
        self.assertEqual([(q["name"], q["description"]) for q in found], [("Ventas d'Andorra", "it's a test")])
        self.assertEqual(found[0]["query"], "SELECT * FROM t WHERE country = 'Andorra'")

    @patch('routes.queries_controller.queriesService.saveSqlQuery')
    def test_save_sql_query_calls_service(self, mock_save):
        dto = SaveQueryRequestDTO(
            query='SELECT 1',
            sqlQueryName='q1',
            description='sample',
        )

        result = queries_controller.saveSqlQuery(dto)
        self.assertIsNone(result)
        mock_save.assert_called_once_with(dto)

    @patch('routes.queries_controller.queriesService.searchQuery')
    def test_search_query_returns_records(self, mock_search):
        mock_search.return_value = pd.DataFrame([
            {'id_query': 1, 'name': 'q1', 'query': 'SELECT 1', 'description': 'sample'}
        ])

        resp = queries_controller.searchQuery('q')
        self.assertEqual(resp.status_code, 200)
        body = self._json(resp)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]['name'], 'q1')

    @patch('routes.queries_controller.queriesService.searchQuery')
    def test_search_query_empty_when_none(self, mock_search):
        mock_search.return_value = None

        resp = queries_controller.searchQuery('missing')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), [])

    @patch('routes.queries_controller.queriesService.deleteQuery')
    def test_delete_query_calls_service(self, mock_delete):
        resp = queries_controller.deleteQuery(12)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), [])
        mock_delete.assert_called_once_with(12)


if __name__ == '__main__':
    unittest.main()
