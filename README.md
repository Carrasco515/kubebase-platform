# KubeBase Platform

> A DevOps **learning and portfolio project** — a local Kubernetes platform lab.
> It runs a small FastAPI demo app on Kubernetes with clean, beginner-friendly
> manifests, Kustomize and GitHub Actions CI.

**KubeBase Platform** is where I practise running and operating an application on
**Kubernetes**. A simple FastAPI service is packaged as a container image and
deployed with plain Kubernetes manifests organised through **Kustomize** — a
Deployment with health probes and resource limits, a Service, a ConfigMap for
non-secret configuration and an example Secret to show the pattern. Everything is
designed to run on a **local cluster** (minikube, kind or Docker Desktop) and is
validated by a read-only CI pipeline.

## Why I built it

After building [CloudBase Lab](https://github.com/Carrasco515/cloudbase-lab) — my
Docker Compose homelab — I wanted to take the next step and learn **Kubernetes**
properly. KubeBase Platform is my hands-on way to understand how an app moves from
a container into a cluster: namespaces, Deployments, Services, configuration,
health probes, resource limits and a clean manifest layout I can grow over time.

## What it demonstrates

- **Containerising an app** with a small, non-root Dockerfile
- **Kubernetes core objects** — Namespace, Deployment, Service, ConfigMap, Secret
- **Health probes** (readiness + liveness) and **resource requests/limits**
- **Configuration management** — non-secret config via ConfigMap, secrets kept
  out of Git (only an example Secret is tracked)
- **Kustomize** for assembling the base deployment
- **CI** with GitHub Actions: Python syntax check, required-file checks and a
  `kubectl kustomize` build — no deployment to a real cluster

## How it complements CloudBase Lab

| | CloudBase Lab | KubeBase Platform |
|---|---|---|
| Orchestration | Docker Compose | Kubernetes |
| Focus | Self-hosted homelab stack | Platform / app-on-Kubernetes lab |
| Config & secrets | `.env` files | ConfigMap + Secret |
| Updates | Watchtower (opt-in) | (roadmap: Helm + GitOps) |

CloudBase Lab shows I can run a real multi-service stack; KubeBase Platform shows
I'm building the **Kubernetes and Platform Engineering** skills on top of that.

## Project layout

```
kubebase-platform/
├── app/                     # FastAPI demo application
│   ├── main.py
│   └── requirements.txt
├── Dockerfile               # Container image for the app
├── kubernetes/base/         # Kustomize base manifests
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secret.example.yaml  # example only — not applied by default
│   └── kustomization.yaml
├── docs/                    # Architecture + operations
└── .github/workflows/ci.yml # Read-only validation
```

## The app

A minimal FastAPI service with three endpoints:

| Endpoint  | Purpose |
|-----------|---------|
| `GET /`        | Welcome message + basic app info |
| `GET /health`  | Health check (used by the liveness/readiness probes) |
| `GET /config`  | Shows the non-secret configuration the app was started with |

Configuration (`APP_NAME`, `APP_ENV`, `APP_GREETING`, `LOG_LEVEL`) is read from
environment variables, which in the cluster come from the **ConfigMap**.

## Run the app locally (without Kubernetes)

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# then open http://localhost:8000/ , /health , /config
```

## Build the Docker image

```bash
docker build -t kubebase-platform:0.1.0 .
docker run --rm -p 8000:8000 kubebase-platform:0.1.0
```

## Deploy to local Kubernetes (later)

> ⚠️ This applies resources to whatever cluster your `kubectl` context points at.
> Make sure it's a **local** cluster first (`kubectl config current-context`).

```bash
# 1. Make the image available to your local cluster, e.g.:
minikube image load kubebase-platform:0.1.0      # minikube
# or: kind load docker-image kubebase-platform:0.1.0   # kind

# 2. Preview the rendered manifests (no changes made):
kubectl kustomize kubernetes/base

# 3. Apply the base (Namespace, ConfigMap, Deployment, Service):
kubectl apply -k kubernetes/base

# 4. Check it came up:
kubectl get pods -n kubebase-dev
```

See [`docs/operations.md`](docs/operations.md) for the full command reference,
including how to reach the Service and how to remove **only this project** safely.

## Roadmap

- [x] **Phase 1** — FastAPI demo app, Dockerfile, base Kubernetes manifests,
  Kustomize, CI
- [ ] **Phase 2** — Kustomize overlays for `dev` / `staging` environments
- [ ] **Phase 3** — Package the app as a **Helm chart**
- [ ] **Phase 4** — **GitOps** delivery (Argo CD or Flux)
- [ ] **Phase 5** — Ingress + TLS, and monitoring (Prometheus / Grafana)

## Documentation

| Document | What it covers |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | App, image, namespace, Deployment, Service, ConfigMap, Secret, and the future Helm/GitOps path |
| [`docs/operations.md`](docs/operations.md) | Day-to-day commands: build, apply, inspect pods, logs, and safe cleanup |

---

*KubeBase Platform is a personal learning project. It runs locally by default and
is not intended for production use as-is.*
