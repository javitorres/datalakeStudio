from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class DualCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware that applies different policies based on the request path:
    - /api/* endpoints: Access-Control-Allow-Origin: * (public APIs)
    - Everything else: only origins listed in allowed_origins
    """

    def __init__(self, app, allowed_origins: list[str] | None = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allow_all = "*" in self.allowed_origins

    def _is_public_api(self, path: str) -> bool:
        return path.startswith("/api/")

    def _get_cors_headers(self, request: Request) -> dict[str, str]:
        origin = request.headers.get("origin", "")
        path = request.url.path

        if self._is_public_api(path):
            return {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "X-Current-Database",
            }

        if self.allow_all or origin in self.allowed_origins:
            return {
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "X-Current-Database",
            }

        return {}

    async def dispatch(self, request: Request, call_next):
        cors_headers = self._get_cors_headers(request)

        if request.method == "OPTIONS":
            return Response(status_code=204, headers=cors_headers)

        try:
            response = await call_next(request)
        except Exception:
            response = Response(status_code=500)

        for key, value in cors_headers.items():
            response.headers[key] = value
        return response
