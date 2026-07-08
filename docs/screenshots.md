# KubeBase Platform — Screenshots & Evidence

All images in `docs/images/` are **real captures** from this repository — no
mock-ups, no invented dashboards. Terminal-style SVGs are rendered from actual
command output with [`docs/scripts/render-terminal-snapshot.py`](scripts/render-terminal-snapshot.py)
(stdlib-only helper, documentation use only).

## Available images

| Image | What it shows | Source |
|---|---|---|
| `images/pytest-results.svg` | Full test suite (`app/test_main.py`) — 4 passed | `pytest -v` in a `python:3.12-slim` container |
| `images/kubernetes-kustomize-build.svg` | Base + dev + prod overlays render cleanly, resource kinds per overlay | `kubectl kustomize kubernetes/...` |
| `images/helm-lint.svg` | Chart lint passes with default and prod values | `helm lint charts/kubebase-api` |
| `images/health-endpoint.svg` | `/health` and `/` responses from the running container | `curl` against `kubebase-platform:dev` |
| `images/metrics-endpoint.svg` | Prometheus metrics (`app_info`, `http_requests_total`, `health_check_total`) | `curl /metrics` against `kubebase-api:observability` |

## How to re-create a snapshot

```bash
# 1. Capture real output to a text file (prefix commands with "$ "):
{ echo '$ helm lint charts/kubebase-api'; helm lint charts/kubebase-api; } > /tmp/helm-lint.txt

# 2. Render it:
python3 docs/scripts/render-terminal-snapshot.py /tmp/helm-lint.txt docs/images/helm-lint.svg "helm lint — charts/kubebase-api"
```

## Pending manual captures

These need a browser session or a logged-in UI and are intentionally **not**
faked:

- [ ] `images/github-actions-ci.png` — capture manually from the GitHub
      Actions tab after a green CI run.
- [ ] `images/fastapi-docs.png` — open `http://localhost:8000/docs` while the
      container runs (`docker run --rm -p 8000:8000 kubebase-api:observability`)
      and screenshot the Swagger UI.
- [ ] `images/argocd-dev-healthy.png` — Argo CD UI showing the dev app
      *Synced / Healthy* (requires a running cluster + Argo CD login).

## Redaction checklist

Before committing any capture:

- [ ] No tokens, passwords, kubeconfig contents or `.env` values visible
- [ ] No private hostnames, e-mail addresses or personal data
- [ ] Trim long outputs — show the meaningful part, not 1000 lines
