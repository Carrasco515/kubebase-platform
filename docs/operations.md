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

## Preview the manifests (no changes made)

```bash
kubectl kustomize kubernetes/base
```

## Apply the manifests

```bash
kubectl apply -k kubernetes/base
```

This creates the `kubebase-dev` namespace, the ConfigMap, the Deployment and the
Service. (The example Secret is **not** applied — see the README.)

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

Edit [`kubernetes/base/configmap.yaml`](../kubernetes/base/configmap.yaml), then:

```bash
kubectl apply -k kubernetes/base
# Restart pods so they pick up the new env values:
kubectl rollout restart deployment/kubebase-api -n kubebase-dev
kubectl rollout status deployment/kubebase-api -n kubebase-dev
```

## Delete ONLY this project from Kubernetes (safe cleanup)

This project lives entirely in the `kubebase-dev` namespace, so cleanup is
scoped and will not touch anything else in the cluster.

```bash
# Option A — remove exactly what Kustomize applied:
kubectl delete -k kubernetes/base

# Option B — delete the whole project namespace (also removes everything in it):
kubectl delete namespace kubebase-dev
```

> ✅ Both options affect **only** `kubebase-dev`. Do **not** run
> `kubectl delete` without a namespace/selector, and never target the
> `default`, `kube-system` or other namespaces.

## Validate manifests without a cluster

```bash
# Render and lint the Kustomize base (what CI runs):
kubectl kustomize kubernetes/base >/dev/null && echo "kustomize build OK"
```
