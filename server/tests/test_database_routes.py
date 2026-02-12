import unittest

import duckdb

from model.QueryRequestDTO import QueryRequest
from routes import database_controller
from services import databaseService


class DatabaseRoutesTest(unittest.TestCase):
    def setUp(self):
        databaseService.db = duckdb.connect(':memory:', config={"allow_unsigned_extensions": "true"})
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
