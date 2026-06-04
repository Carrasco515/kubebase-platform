# KubeBase Platform — Operations

Day-to-day commands for building, deploying and inspecting the demo app on a
**local** Kubernetes cluster. Run them from the project root
(`~/projects/kubebase-platform`) unless noted.

> ⚠️ **Always check your cluster context first.** These commands act on whatever
> cluster `kubectl` currently points at. Confirm it is a local cluster before
> applying anything:
>
> ```bash
> kubectl config current-context
> ```

---

## Run the app locally (no Kubernetes)

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# http://localhost:8000/  ,  /health  ,  /config
```

## Build the Docker image

```bash
docker build -t kubebase-platform:0.1.0 .

# Quick smoke test outside Kubernetes:
docker run --rm -p 8000:8000 kubebase-platform:0.1.0
```

## Make the image available to the local cluster

A locally built image must be loaded into the cluster (it is not pushed to a
registry):

```bash
# minikube
minikube image load kubebase-platform:0.1.0

# kind
kind load docker-image kubebase-platform:0.1.0

# Docker Desktop Kubernetes uses the local Docker images directly.
```

## Environments (Kustomize)

The project has a shared `base` and two overlays:

| Target | Namespace | Replicas | Purpose |
|---|---|---|---|
| `kubernetes/base` | `kubebase-dev` | 2 | Shared manifests (also usable directly) |
| `kubernetes/overlays/dev` | `kubebase-dev` | 2 | Local development on Minikube |
| `kubernetes/overlays/prod` | `kubebase-prod` | 3 | **Local learning "prod"** — not a real production cluster |

> ⚠️ The **prod** overlay is only a local exercise in running a second
> environment. It is **not** a real production deployment, holds no real secrets
> and no real data. Apply it only when you are deliberately testing it.

## Preview the manifests (no changes made)

```bash
kubectl kustomize kubernetes/base
kubectl kustomize kubernetes/overlays/dev
kubectl kustomize kubernetes/overlays/prod
```

## Apply — dev

```bash
kubectl apply -k kubernetes/overlays/dev

# Check it came up:
kubectl get all -n kubebase-dev
```

This creates/updates the `kubebase-dev` namespace, the ConfigMap, the Deployment
and the Service. (The example Secret is **not** applied — see the README.)

## Apply — prod (only when intentionally testing)

```bash
kubectl apply -k kubernetes/overlays/prod

# Check it came up:
kubectl get all -n kubebase-prod
```

> Applies into the separate `kubebase-prod` namespace. Remember the image must
> be loaded into the cluster first (same `minikube image load` step as dev).

## Helm (packaging path)

The app is also packaged as a Helm chart at `charts/kubebase-api`. Kustomize
remains the raw-manifest + overlay learning path; Helm is the packaging and
templating path. Both deploy the same app — **don't run both into the same
namespace at once**, as they manage overlapping objects.

### Render (no changes made)

```bash
helm template kubebase-api charts/kubebase-api
helm template kubebase-api charts/kubebase-api -f charts/kubebase-api/values-dev.yaml
helm template kubebase-api charts/kubebase-api -f charts/kubebase-api/values-prod.yaml
```

### Lint

```bash
helm lint charts/kubebase-api
```

### Install / upgrade — dev (only when intentionally testing)

```bash
helm upgrade --install kubebase-api charts/kubebase-api \
  -n kubebase-dev --create-namespace \
  -f charts/kubebase-api/values-dev.yaml

# Check and reach it:
kubectl get all -n kubebase-dev
kubectl port-forward -n kubebase-dev svc/kubebase-api 8080:80
```

### Uninstall — dev

```bash
helm uninstall kubebase-api -n kubebase-dev
```

> The **prod** values are a local learning profile — render-only unless you
> deliberately test them. The chart's example Secret is **disabled by default**
> (`secret.enabled=false`) and contains placeholders only — never put real
> secrets in values files.

## Check pods and resources

```bash
# Pods in this project's namespace
kubectl get pods -n kubebase-dev

# Everything this project created
kubectl get all -n kubebase-dev

# Detailed view of one pod (events, probe status, restarts)
kubectl describe pod -n kubebase-dev -l app.kubernetes.io/name=kubebase-platform

# Are the ConfigMap and Service there?
kubectl get configmap,svc -n kubebase-dev
```

## View logs

```bash
# Logs from all app pods (by label), follow live
kubectl logs -n kubebase-dev -l app.kubernetes.io/name=kubebase-platform -f

# Logs from a single named pod
kubectl logs -n kubebase-dev <pod-name>
```

## Reach the app

The Service is `ClusterIP` (internal). Use a port-forward for local access:

```bash
kubectl port-forward -n kubebase-dev svc/kubebase-api 8080:80
# then open http://localhost:8080/  ,  /health  ,  /config
```

## Apply a change to config

Edit the base ConfigMap ([`kubernetes/base/configmap.yaml`](../kubernetes/base/configmap.yaml))
or the per-environment patch
([`kubernetes/overlays/dev/configmap-patch.yaml`](../kubernetes/overlays/dev/configmap-patch.yaml)),
then re-apply the overlay:

```bash
kubectl apply -k kubernetes/overlays/dev
# Restart pods so they pick up the new env values:
kubectl rollout restart deployment/kubebase-api -n kubebase-dev
kubectl rollout status deployment/kubebase-api -n kubebase-dev
```

## Delete ONLY this project from Kubernetes (safe cleanup)

This project lives entirely in its own namespaces (`kubebase-dev` and, if you
applied it, `kubebase-prod`), so cleanup is scoped and will not touch anything
else in the cluster.

```bash
# Remove exactly what each overlay applied:
kubectl delete -k kubernetes/overlays/dev     # removes the dev resources
kubectl delete -k kubernetes/overlays/prod    # removes the prod resources (if applied)

# Or delete a whole project namespace (also removes everything in it):
kubectl delete namespace kubebase-dev
kubectl delete namespace kubebase-prod
```

> ✅ All of these affect **only** `kubebase-dev` / `kubebase-prod`. Do **not**
> run `kubectl delete` without a namespace/selector, and never target the
> `default`, `kube-system` or other namespaces.

## Validate manifests without a cluster

```bash
# Render the base and both overlays (what CI runs):
for d in kubernetes/base kubernetes/overlays/dev kubernetes/overlays/prod; do
  kubectl kustomize "$d" >/dev/null && echo "kustomize build OK: $d"
done

# Lint and render the Helm chart (default + both profiles):
helm lint charts/kubebase-api
helm template kubebase-api charts/kubebase-api >/dev/null && echo "helm OK: default"
helm template kubebase-api charts/kubebase-api -f charts/kubebase-api/values-dev.yaml  >/dev/null && echo "helm OK: dev"
helm template kubebase-api charts/kubebase-api -f charts/kubebase-api/values-prod.yaml >/dev/null && echo "helm OK: prod"
```
