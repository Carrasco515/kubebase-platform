# KubeBase Platform — Architecture

## Purpose

KubeBase Platform is a **local Kubernetes platform lab**. It takes a small
application all the way from source code to running Pods on a cluster, using the
core Kubernetes objects and a clean, Kustomize-based manifest layout. It is a
learning and portfolio project and runs **locally by default** (minikube, kind or
Docker Desktop) — it is not a production platform.

## Overview

```
Source code (FastAPI)  ->  Container image (Dockerfile)  ->  Kubernetes (Kustomize base)
                                                              ├─ Namespace: kubebase-dev
                                                              ├─ ConfigMap  (non-secret config)
                                                              ├─ Secret     (example only)
                                                              ├─ Deployment (2 replicas, probes, limits)
                                                              └─ Service    (ClusterIP :80 -> :8000)
```

## Components

### App

A minimal **FastAPI** service (`app/main.py`) with three endpoints: `/` (info),
`/health` (probe target) and `/config` (the non-secret configuration it sees). It
reads `APP_NAME`, `APP_ENV`, `APP_GREETING` and `LOG_LEVEL` from environment
variables, with safe defaults so it also runs without any configuration. It never
reads or returns secret values.

### Container image

The [`Dockerfile`](../Dockerfile) builds a single-stage image on `python:3.12-slim`.
It installs the dependencies first (for layer caching), copies the app, runs as a
non-root user (`uid 10001`) and serves the app with `uvicorn` on port `8000`.
Tagged `kubebase-platform:0.1.0` for local use.

### Kubernetes namespace

All objects live in the **`kubebase-dev`** namespace
([`namespace.yaml`](../kubernetes/base/namespace.yaml)). Keeping the project in
its own namespace makes it easy to inspect and to remove cleanly without touching
anything else in the cluster.

### Deployment

[`deployment.yaml`](../kubernetes/base/deployment.yaml) runs **2 replicas** of the
app container. It defines:

- a named `http` port (`8000`),
- `envFrom` the **ConfigMap** so config arrives as environment variables,
- a **readinessProbe** and **livenessProbe** on `/health` (readiness gates
  traffic; liveness restarts a stuck container),
- **resource requests and limits** (`50m`/`64Mi` requested, `200m`/`128Mi`
  limit) so the scheduler can place it and it can't starve the node.

### Service

[`service.yaml`](../kubernetes/base/service.yaml) is a **ClusterIP** Service that
exposes the Deployment inside the cluster on port `80`, forwarding to the
container's `http` (`8000`) port. ClusterIP keeps it internal; for local access
you use `kubectl port-forward` (see operations) — external exposure via Ingress
is on the roadmap.

### ConfigMap

[`configmap.yaml`](../kubernetes/base/configmap.yaml) holds the **non-secret**
configuration (`APP_NAME`, `APP_ENV`, `APP_GREETING`, `LOG_LEVEL`). It is the
single place to change the app's behaviour without rebuilding the image.

### Secret (example only)

[`secret.example.yaml`](../kubernetes/base/secret.example.yaml) shows the **shape**
of a Kubernetes Secret with obvious placeholder values. It is **not** applied by
the Kustomize base and the demo app does not need it. To use a real secret, copy
it to a local, git-ignored `secret.yaml`, fill in your own values and add it to
the kustomization yourself. Real secrets must never be committed.

### Kustomize base

[`kustomization.yaml`](../kubernetes/base/kustomization.yaml) ties the resources
together, pins the `kubebase-dev` namespace and adds a common `part-of` label.
`kubectl kustomize kubernetes/base` renders the full set of manifests; CI runs
exactly this to validate them.

## CI

A GitHub Actions workflow ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml))
validates the project on every push/PR — **read-only**: it checks Python syntax,
verifies required files exist, confirms Kubernetes YAML is present and builds the
Kustomize base with `kubectl kustomize`. It does **not** build/push images or
deploy to any cluster.

## Future Helm and GitOps path

The project demonstrates a realistic progression of delivery tooling:

```
App (FastAPI)  ->  Docker image  ->  Kubernetes manifests  ->  Kustomize overlays  ->  Helm chart
```

- **Kustomize** (Phase 2) — raw manifests plus `dev`/`prod` overlays that patch
  the base's config and replica count without duplicating it.
- **Helm** (Phase 3) — the same app packaged as a chart (`charts/kubebase-api`)
  with `values.yaml` and `values-dev.yaml` / `values-prod.yaml` profiles. Helm
  is the **packaging/templating** path; Kustomize stays as the raw-manifest
  learning path. Both deploy the same app (don't run both into one namespace at
  once). The chart's example Secret is disabled by default (placeholders only).

Planned evolution from here:

1. **More overlays / chart values** — additional per-environment differences
   (image tags, extra config), and possibly a `staging` profile.
2. **GitOps** — deliver the chart/manifests declaratively with **Argo CD** or
   **Flux**, so the cluster state always matches Git.
3. **Ingress + TLS and monitoring** — expose the Service through an Ingress
   controller and add Prometheus/Grafana observability.

This mirrors a realistic progression from raw manifests → Kustomize → Helm →
GitOps that Platform Engineering teams use in practice.
