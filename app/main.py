"""KubeBase Platform — demo FastAPI application.

A small, deliberately simple service used to practise running and operating an
app on Kubernetes. It reads its (non-secret) configuration from environment
variables, which in the cluster are injected from a ConfigMap.

Endpoints:
    GET /        — welcome message + basic app info
    GET /health  — liveness/readiness probe target
    GET /config  — the non-secret configuration the app sees
    GET /metrics — Prometheus-format metrics (Phase 5 observability)

No secrets are read or returned here. Secret values (if any) belong in a
Kubernetes Secret and must never be exposed through an endpoint — and metrics
must never contain secret values either.
"""

import os
import time

from fastapi import FastAPI, Request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    Info,
    generate_latest,
)
from starlette.responses import Response

# Read non-secret configuration from the environment. In Kubernetes these come
# from the ConfigMap (see kubernetes/base/configmap.yaml). Sensible defaults
# keep the app runnable locally without any configuration.
APP_NAME = os.getenv("APP_NAME", "KubeBase Platform")
APP_ENV = os.getenv("APP_ENV", "local")
APP_GREETING = os.getenv("APP_GREETING", "Hello from KubeBase Platform!")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

app = FastAPI(title=APP_NAME)

# --- Prometheus metrics -----------------------------------------------------
# A few small, beginner-friendly metrics. The Prometheus client also exposes
# default process_* / python_* metrics automatically. No secret values are ever
# recorded as metric values or labels.

# app_info: a single constant-value series carrying app metadata as labels.
APP_INFO = Info("app", "KubeBase Platform application metadata")
APP_INFO.info({"app_name": APP_NAME, "environment": APP_ENV})

# http_requests_total: how many requests we served, split by method/path/status.
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests handled.",
    ["method", "path", "status"],
)

# http_request_duration_seconds: how long requests took (default buckets).
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)

# health_check_total: how often the health endpoint was hit (probes use it).
HEALTH_CHECK_COUNT = Counter(
    "health_check_total",
    "Total number of /health requests served.",
)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    """Record count + duration for each request.

    The scrape of ``/metrics`` itself is intentionally not counted, to keep the
    request signal about the app rather than about Prometheus. We label by the
    raw request path; this app has a small, fixed set of routes, so label
    cardinality stays low. (A larger app would label by the matched route
    template instead, to avoid unbounded cardinality from unknown paths.)
    """
    if request.url.path == "/metrics":
        return await call_next(request)

    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    path = request.url.path
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    return response


@app.get("/")
def root():
    """Welcome message with basic, non-sensitive app info."""
    return {
        "message": APP_GREETING,
        "app": APP_NAME,
        "environment": APP_ENV,
    }


@app.get("/health")
def health():
    """Health check used by the Kubernetes liveness and readiness probes."""
    HEALTH_CHECK_COUNT.inc()
    return {"status": "ok"}


@app.get("/config")
def config():
    """Expose only the non-secret configuration the app was started with.

    This intentionally returns ConfigMap-style values only — never anything
    that would live in a Secret.
    """
    return {
        "app_name": APP_NAME,
        "app_env": APP_ENV,
        "greeting": APP_GREETING,
        "log_level": LOG_LEVEL,
    }


@app.get("/metrics")
def metrics():
    """Expose metrics in the Prometheus text exposition format.

    Prometheus (or any compatible scraper) reads this endpoint. It contains only
    operational counters/gauges — never secrets or request bodies.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
