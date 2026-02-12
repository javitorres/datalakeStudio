import json
import unittest
from unittest.mock import patch

from model.Metadata import Metadata
from routes import s3_controller


def _endpoint_by_path(path: str):
    for route in s3_controller.router.routes:
        if route.path == path:
            return route.endpoint
    raise AssertionError(f'Route not found: {path}')


class S3ControllerTest(unittest.TestCase):
    @patch('routes.s3_controller.s3Service.s3Search')
    def test_s3_search_short_term_skips_service(self, mock_search):
        resp = s3_controller.s3Search('my-bucket', 'ab')
        self.assertEqual(resp, {'results': []})
        mock_search.assert_not_called()

    @patch('routes.s3_controller.s3Service.s3Search')
    def test_s3_search_truncates_results(self, mock_search):
        mock_search.return_value = [f'f{i}' for i in range(20)]

        resp = s3_controller.s3Search('my-bucket', 'file')
        self.assertEqual(len(resp['results']), 10)

    @patch('routes.s3_controller.s3Service.getContent')
    def test_get_content_ok(self, mock_content):
        mock_content.return_value = {'content': ['a.csv'], 'metadata': None}
        endpoint = _endpoint_by_path('/s3/getContent')

        resp = endpoint('my-bucket', '')
        self.assertEqual(resp, {'content': ['a.csv'], 'metadata': None})

    @patch('routes.s3_controller.s3Service.getFilePreview')
    def test_get_file_preview_ok(self, mock_preview):
        mock_preview.return_value = [b'preview']
        endpoint = _endpoint_by_path('/s3/getFilePreview')

        resp = endpoint('my-bucket', 'x.csv')
        self.assertEqual(resp, [b'preview'])

    @patch('routes.s3_controller.s3Service.updateMetadata', return_value=True)
    def test_update_metadata_ok(self, _mock_update):
        metadata = Metadata(description='d', owner='o', schema='s', bucket='b', path='p/')
        resp = s3_controller.updateMetadata(metadata)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.body.decode('utf-8'))
        self.assertEqual(body['status'], 'ok')

    @patch('routes.s3_controller.s3Service.updateMetadata', return_value=False)
    def test_update_metadata_error(self, _mock_update):
        metadata = Metadata(description='d', owner='o', schema='s', bucket='b', path='p/')
        resp = s3_controller.updateMetadata(metadata)
        self.assertEqual(resp.status_code, 400)


if __name__ == '__main__':
    unittest.main()
