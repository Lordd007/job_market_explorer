from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from time import perf_counter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

REQS = Counter("http_requests_total", "HTTP requests", ["method","path","status"])
LAT  = Histogram("http_request_duration_seconds", "Latency", ["method","path"])

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = perf_counter()
        resp = await call_next(request)
        dur  = perf_counter() - start
        path = request.url.path
        REQS.labels(request.method, path, str(resp.status_code)).inc()
        LAT.labels(request.method, path).observe(dur)
        return resp

async def metrics_endpoint(_req):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
