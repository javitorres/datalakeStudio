import asyncio
import json
import unittest
from unittest.mock import patch

from model.apiEnrichmentRequestDTO import ApiEnrichmentRequestDTO
from routes import apiretriever_controller


class _FakeConfig:
    def __init__(self):
        self.get_secrets = {
            'api_domain': 'example.com',
            'api_context': 'ctx',
        }


class ApiRetrieverControllerTest(unittest.TestCase):
    @staticmethod
    def _json(response):
        return json.loads(response.body.decode('utf-8'))

    @patch('routes.apiretriever_controller.apiRetrieverService.getServices', return_value=['svc-a'])
    def test_get_services(self, _mock_services):
        resp = apiretriever_controller.getServices('svc')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), ['svc-a'])

    @patch('routes.apiretriever_controller.Config.get_instance', return_value=_FakeConfig())
    @patch('routes.apiretriever_controller.apiRetrieverService.getRepositoryMethodList')
    def test_get_repository_method_list_uses_defaults(self, mock_methods, _mock_cfg):
        mock_methods.return_value = [{'path': '/cars'}]

        resp = apiretriever_controller.getRepositoryMethodList('svc', '/car')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), [{'path': '/cars'}])
        mock_methods.assert_called_once_with('svc', '/car', 'pro', 'example.com', 'ctx')

    @patch('routes.apiretriever_controller.Config.get_instance', return_value=_FakeConfig())
    @patch('routes.apiretriever_controller.apiRetrieverService.getMethodInfo')
    def test_get_method_info_uses_defaults(self, mock_info, _mock_cfg):
        mock_info.return_value = {'method': 'GET', 'url': 'http://svc.pro.example.com/cars'}

        resp = apiretriever_controller.getMethodInfo('svc', '/cars', 'GET')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp)['method'], 'GET')
        mock_info.assert_called_once_with('svc', '/cars', 'GET', 'pro', 'example.com', 'ctx')

    @patch('routes.apiretriever_controller.Config.get_instance', return_value=_FakeConfig())
    @patch('routes.apiretriever_controller.apiRetrieverService.runApiEnrichment')
    def test_run_api_enrichment(self, mock_run, _mock_cfg):
        dto = ApiEnrichmentRequestDTO(
            tableName='iris',
            parameters={'id': 'id'},
            mappings=[{'jsonField': 'name', 'newFieldName': 'api_name'}],
            recordsToProcess=10,
            service='svc',
            method={'controller': 'c', 'method': 'GET', 'path': '/cars'},
            url='http://svc.pro.example.com/cars',
            newTableName='iris_enriched',
        )

        resp = asyncio.run(apiretriever_controller.runApiEnrichment(dto))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._json(resp), 'OK')
        mock_run.assert_called_once_with(dto, 'example.com', 'pro')


if __name__ == '__main__':
    unittest.main()
