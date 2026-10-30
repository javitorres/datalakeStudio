import asyncio
import unittest

import httpx
from fastapi import FastAPI

from middleware.cors_middleware import DualCORSMiddleware


class DualCORSMiddlewareTest(unittest.TestCase):
    def test_unhandled_errors_are_logged_and_returned_as_json(self):
        app = FastAPI()
        app.add_middleware(DualCORSMiddleware, allowed_origins=["http://localhost:8080"])

        @app.get("/boom")
        def boom():
            raise RuntimeError("boom")

        async def call():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                return await client.get("/boom", headers={"Origin": "http://localhost:8080"})

        with self.assertLogs(level="ERROR") as logs:
            response = asyncio.run(call())

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"status": "error", "message": "boom"})
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:8080")
        self.assertIn("Unhandled error in GET /boom", logs.output[0])
        self.assertIsNotNone(logs.records[0].exc_info)


if __name__ == '__main__':
    unittest.main()
