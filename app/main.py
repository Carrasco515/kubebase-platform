"""KubeBase Platform — demo FastAPI application.

A small, deliberately simple service used to practise running and operating an
app on Kubernetes. It reads its (non-secret) configuration from environment
variables, which in the cluster are injected from a ConfigMap.

Endpoints:
    GET /        — welcome message + basic app info
    GET /health  — liveness/readiness probe target
    GET /config  — the non-secret configuration the app sees

No secrets are read or returned here. Secret values (if any) belong in a
Kubernetes Secret and must never be exposed through an endpoint.
"""

import os

from fastapi import FastAPI

# Read non-secret configuration from the environment. In Kubernetes these come
# from the ConfigMap (see kubernetes/base/configmap.yaml). Sensible defaults
# keep the app runnable locally without any configuration.
APP_NAME = os.getenv("APP_NAME", "KubeBase Platform")
APP_ENV = os.getenv("APP_ENV", "local")
APP_GREETING = os.getenv("APP_GREETING", "Hello from KubeBase Platform!")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

app = FastAPI(title=APP_NAME)


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
