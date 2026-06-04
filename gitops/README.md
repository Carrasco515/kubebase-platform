# GitOps (Argo CD) — KubeBase Platform

This folder contains **GitOps** examples: Argo CD `Application` manifests that
describe how the project's Helm chart would be deployed from Git.

> ⚠️ These are **preparation/example** files. Nothing here is applied
> automatically, and they do nothing until Argo CD is installed in a cluster.
> See [`../docs/gitops.md`](../docs/gitops.md) for the full workflow and safe
> testing steps.

## What GitOps means (in simple terms)

GitOps means **Git is the source of truth** for what should run in the cluster.
Instead of running `kubectl apply` or `helm install` by hand, you commit the
desired state to Git, and a controller (here, **Argo CD**) continuously compares
Git ("desired state") to the cluster ("live state") and reconciles the two.

- You change Git → Argo CD notices the difference.
- Depending on the sync policy, Argo CD either **waits for you to sync** (manual)
  or **applies the change itself** (automated).

## What these files do

| File | Purpose |
|---|---|
| [`argocd/kubebase-api-dev.yaml`](argocd/kubebase-api-dev.yaml) | Argo CD Application that deploys the Helm chart into `kubebase-dev` using `values-dev.yaml` |
| [`argocd/kubebase-api-prod.yaml`](argocd/kubebase-api-prod.yaml) | **Example-only** Application that would deploy into `kubebase-prod` using `values-prod.yaml` |

Each Application points at this repository
(`https://github.com/Carrasco515/kubebase-platform.git`, branch `main`), the
chart path `charts/kubebase-api`, and the matching values file.

## How Argo CD would use the Helm chart

Argo CD reads the `Application`, fetches the repo at `targetRevision: main`,
renders the Helm chart at `path: charts/kubebase-api` with the chosen
`valueFiles`, and compares the result to what's running in the destination
namespace. With manual sync (the default here) it only **reports** drift; you
trigger the actual apply with the Argo CD UI or `argocd app sync`.

This reuses the **exact same chart** tested in Phase 3 — GitOps is just a
different *delivery* mechanism, not a different app.

## Why the project has both Kustomize and Helm

The project deliberately demonstrates a progression of delivery tooling:

- **Kustomize** — learn the raw Kubernetes objects and per-environment overlays.
- **Helm** — package the same app as a versioned, templated chart with values.
- **GitOps (Argo CD)** — deploy that chart declaratively, with Git as the source
  of truth.

They are complementary learning paths, not competitors.

## Why dev and prod are separated

Each environment is its own Argo CD Application, its own namespace
(`kubebase-dev` / `kubebase-prod`) and its own values file. This mirrors real
setups where environments are isolated and promoted independently — and it keeps
a change to one environment from affecting the other.

## Why prod is example only

`kubebase-api-prod.yaml` is a **local learning** example, not a real production
environment. It has **no** automated sync, holds **no** real secrets, and should
only ever be applied deliberately while practising. Treat the dev Application as
the one you actually exercise locally.
