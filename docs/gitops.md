# KubeBase Platform — GitOps with Argo CD

This document explains the GitOps workflow used by the example Argo CD
Applications in [`../gitops/argocd/`](../gitops/argocd/). It is **Phase 4
preparation**: it shows how the project's Helm chart *would* be delivered with
GitOps. No Argo CD installation or apply is required to read or validate it.

> ⚠️ **Safety:** Nothing in this phase changes a cluster. Do not install Argo CD
> or apply the Application manifests unless you deliberately choose to. Prod is
> an example only.

---

## GitOps workflow

1. **Desired state lives in Git.** The Helm chart (`charts/kubebase-api`) and its
   values files describe what should run.
2. **Argo CD watches the repo.** An `Application` object tells Argo CD which
   repo, revision, chart path and values to use, and which namespace to target.
3. **Argo CD compares desired vs. live.** It renders the chart and diffs the
   result against the cluster.
4. **Reconciliation.** With **manual** sync (the default here), Argo CD reports
   `OutOfSync` and waits for you to sync. With **automated** sync (opt-in), it
   applies changes itself.

## Repository as the source of truth

The cluster should reflect what's in Git — not the other way around. You change
the app by committing to `main`; you do **not** hand-edit live resources. This
makes deployments reviewable (pull requests), auditable (git history) and
repeatable (the same commit produces the same state).

## Desired state vs. live state

- **Desired state** = the rendered Helm chart at `targetRevision: main`.
- **Live state** = what is actually running in `kubebase-dev` / `kubebase-prod`.

Argo CD continuously computes the difference. Manual sync means *you* decide when
to close the gap; automated sync means Argo CD closes it for you.

## Validate before any cluster apply (render-only)

Always confirm the chart renders before involving a cluster — this is exactly
what CI does and never touches a cluster:

```bash
# Helm chart renders (default + both profiles):
helm lint charts/kubebase-api
helm template kubebase-api charts/kubebase-api -f charts/kubebase-api/values-dev.yaml
helm template kubebase-api charts/kubebase-api -f charts/kubebase-api/values-prod.yaml

# Argo CD Application YAML is present and well-formed (structure check):
for f in gitops/argocd/kubebase-api-dev.yaml gitops/argocd/kubebase-api-prod.yaml; do
  test -f "$f" && grep -q 'kind: Application' "$f" && echo "OK: $f"
done
```

> `kubectl` cannot fully validate `kind: Application` without the Argo CD CRDs
> installed, so a presence + structure check is the safe local/CI validation.

## Dev Application

[`gitops/argocd/kubebase-api-dev.yaml`](../gitops/argocd/kubebase-api-dev.yaml):

- **repoURL:** `https://github.com/Carrasco515/kubebase-platform.git`
- **targetRevision:** `main`
- **path:** `charts/kubebase-api`, **valueFiles:** `values-dev.yaml`
- **destination namespace:** `kubebase-dev`
- **sync:** manual (no `automated` block); `CreateNamespace=true` is set

It would deploy the dev profile (replicas 2, `APP_ENV=dev`, `LOG_LEVEL=debug`)
and report drift, but only sync when you tell it to.

## Prod Application (example only)

[`gitops/argocd/kubebase-api-prod.yaml`](../gitops/argocd/kubebase-api-prod.yaml):

- Same repo/revision/chart, **valueFiles:** `values-prod.yaml`
- **destination namespace:** `kubebase-prod`
- **sync:** manual; **no** automated sync — never auto-sync a prod example
- **Example only.** Do not apply without explicit, deliberate intent. No real
  secrets.

## Safe testing approach

Only after you *choose* to install Argo CD (out of scope for this phase):

```bash
# 1. (You decide to) install Argo CD into the argocd namespace — see Argo CD docs.
#    This phase does NOT do this for you.

# 2. Apply the DEV Application object (registers it with Argo CD; sync is manual):
kubectl apply -f gitops/argocd/kubebase-api-dev.yaml

# 3. Watch it and sync deliberately (UI or CLI):
#    argocd app get kubebase-api-dev
#    argocd app sync kubebase-api-dev

# 4. Verify the workload:
kubectl get all -n kubebase-dev
kubectl port-forward -n kubebase-dev svc/kubebase-api 8080:80
```

> Reminder: the Kustomize dev overlay and a Helm/Argo CD dev release both manage
> objects named `kubebase-api` in `kubebase-dev`. Don't run two managers against
> the same namespace at once — pick one, or use a separate namespace.

## Cleanup commands

```bash
# Remove the Argo CD Application (this alone may leave the workload running,
# depending on sync/prune settings):
kubectl delete -f gitops/argocd/kubebase-api-dev.yaml

# If a dev workload was synced and you want it gone, remove it the same way you
# created it (e.g. helm uninstall, or delete the namespace you created for it).
```

> Do **not** delete the shared `kubebase-dev` namespace if your Kustomize dev
> deployment is still using it. Only remove what you created for the GitOps test.

## Risks and safety notes

- **Automated sync changes the cluster on its own.** It's disabled by default
  here; enable `automated.prune` / `automated.selfHeal` only once you understand
  them. `prune` deletes resources removed from Git; `selfHeal` reverts manual
  changes.
- **Two managers, one namespace** (Kustomize + GitOps) will fight over the same
  objects. Keep them separate.
- **Prod is an example**, not a real environment — apply only deliberately.
- **No secrets in Git.** These manifests contain none, and the chart's example
  Secret stays disabled with placeholder values only.
