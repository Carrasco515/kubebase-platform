# syntax=docker/dockerfile:1
#
# KubeBase Platform — demo FastAPI image.
# Small, single-stage image based on the slim Python runtime. Runs as a
# non-root user and serves the app with uvicorn on port 8000.

FROM python:3.12-slim

# Don't write .pyc files, and stream logs straight to stdout/stderr so that
# `kubectl logs` shows output immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached when only app code changes.
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY app/ ./app/

# Run as an unprivileged user (good practice; required by some cluster policies).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Start the API. The container listens on all interfaces inside the pod.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
