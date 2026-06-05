# KubeBase Platform — Observability (Phase 5)

This document covers the **observability** layer added in Phase 5: a
Prometheus-compatible `/metrics` endpoint on the app, the Kubernetes/Helm
metadata that makes scraping easy later, and how Prometheus and Grafana would
fit in.

> ⚠️ **Nothing here installs Prometheus or Grafana, and nothing changes a
> cluster.** Phase 5 makes the app *observability-ready*. Running a real
> monitoring stack is an explicit, opt-in future step.

---

## What "observability" means (in simple terms)

Observability is being able to understand what your app is doing from the
outside, using the signals it emits. The three classic signals are:

- **Metrics** — small numbers over time (request rate, error count, latency).
  Cheap to store, great for dashboards and alerts. **This is what Phase 5 adds.**
- **Logs** — text records of individual events. Good for detail and debugging.
- **Traces** — the path of a single request across services (not used here).

Metrics answer "how much / how many / how fast" at a glance; logs answer "what
exactly happened in this one case".

## How metrics differ from logs and health checks

| Signal | Question it answers | Example here |
|---|---|---|
| **Health check** (`/health`) | Is the app alive *right now*? | Used by the liveness/readiness probes |
| **Logs** (`kubectl logs`) | What happened in this specific event? | A stack trace, a request line |
| **Metrics** (`/metrics`) | What are the trends over time? | Requests/sec, p95 latency, error ratio |

The health check is a yes/no for Kubernetes; metrics are numbers for humans and
dashboards. They complement each other — Phase 5 adds the metrics piece.

## What `/metrics` exposes

The app serves Prometheus text-format metrics at **`GET /metrics`**. The
project-specific metrics are:

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `app_info` | info/gauge | `app_name`, `environment` | Constant `1`; carries app metadata as labels |
| `http_requests_total` | counter | `method`, `path`, `status` | Number of HTTP requests handled |
| `http_request_duration_seconds` | histogram | `method`, `path` | Request latency (buckets + `_count` + `_sum`) |
| `health_check_total` | counter | — | Number of `/health` requests served |

In addition, the Prometheus client library automatically exposes default
`process_*` and `python_*` metrics (CPU, memory, open FDs, GC, etc.).

> 🔒 **No secrets in metrics.** Metric names, labels and values contain only
> operational data — never tokens, passwords, request bodies or config secrets.

The scrape of `/metrics` itself is intentionally **not** counted in
`http_requests_total`, so the request numbers describe real app traffic rather
than Prometheus polling.

## How Prometheus would scrape the app

Prometheus periodically does an HTTP GET on each target's `/metrics` and stores
the numbers as time series. The pods carry plain scrape-hint annotations (added
in this phase):

```yaml
prometheus.io/scrape: "true"
prometheus.io/path: "/metrics"
prometheus.io/port: "8000"
```

- These are **just annotations**. They need **no** Prometheus Operator and **no**
  CRDs. A cluster with no monitoring installed simply ignores them.
- A Prometheus configured with a `kubernetes_sd_configs` pod-discovery job reads
  these annotations and starts scraping the pod — no per-app Prometheus config.
- The Helm chart gates them behind `metrics.enabled` (default `true`); the
  Kustomize base sets them directly. See the values below.

If you later run the Prometheus **Operator**, the modern alternative is a
`ServiceMonitor`/`PodMonitor` CRD object. We do **not** ship one here, because it
would fail to apply on a cluster (or in CI) that lacks the CRD. It's noted as a
future option only.

## How Grafana would use Prometheus data

Grafana does not store metrics — it **queries Prometheus** (its data source) with
PromQL and draws panels. Typical queries against these metrics:

```promql
# Request rate per path
sum by (path) (rate(http_requests_total[5m]))

# 95th-percentile latency per path
histogram_quantile(0.95, sum by (le, path) (rate(http_request_duration_seconds_bucket[5m])))

# Error ratio (5xx share of all requests)
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

A **starter dashboard** is provided at
[`../observability/grafana/kubebase-api-dashboard.json`](../observability/grafana/kubebase-api-dashboard.json).
It is generic and safe: it does **not** hardcode a Prometheus URL. On import you
pick your Prometheus data source for its `DS_PROMETHEUS` variable.

## Test metrics locally (no Kubernetes)

```bash
# Run the app directly:
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# In another terminal — generate some traffic, then read metrics:
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/config
curl http://localhost:8000/metrics
```

Or with Docker:

```bash
docker build -t kubebase-api:observability .
docker run --rm -d --name kubebase-api-metrics-test -p 8001:8000 kubebase-api:observability
curl http://localhost:8001/metrics
docker rm -f kubebase-api-metrics-test   # removes only this test container
```

## Test metrics in Kubernetes (via port-forward)

After deploying the app (Kustomize or Helm) into `kubebase-dev`:

```bash
# Confirm the scrape annotations are on the pods:
kubectl get pod -n kubebase-dev \
  -l app.kubernetes.io/name=kubebase-platform \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.prometheus\.io/scrape}{"\n"}{end}'

# Reach the Service and read /metrics:
kubectl port-forward -n kubebase-dev svc/kubebase-api 8080:80   # Kustomize service name
# (Helm release service is svc/kubebase-api-dev — adjust the name accordingly)
curl http://localhost:8080/metrics
```

## Why no real Prometheus or Grafana is installed yet

This phase keeps the cluster footprint small and the project safe to run
anywhere (including CI, which has no monitoring stack):

- The app is **scrape-ready** without forcing anyone to run a monitoring stack.
- No CRDs are required, so manifests apply on a plain cluster and CI stays green.
- Installing Prometheus/Grafana is a deliberate decision with real resource cost,
  so it is left as an explicit opt-in.

## Future path: a real monitoring stack

When you choose to run monitoring locally, the common options are:

- **kube-prometheus-stack** (Prometheus Community Helm chart) — bundles
  Prometheus, Alertmanager and Grafana with sensible defaults and the Operator.
  ```bash
  # Example only — do NOT run unless you intend to install monitoring:
  # helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  # helm repo update
  # helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
  ```
- Then either keep the annotation-based pod scraping, or add a `PodMonitor`/
  `ServiceMonitor` (now that the CRDs exist) to target this app, and import the
  starter dashboard into Grafana.

See the [roadmap](../README.md#roadmap) — this is **Phase 5 (observability
layer)**; a fully running monitoring stack remains a future, opt-in step.
