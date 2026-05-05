# AutoHealOps Local Kubernetes Manifests

These manifests deploy AutoHealOps to a local Kubernetes cluster such as `k3d`, `kind`, or local K3s with:

- ConfigMap and Secret-based configuration
- readiness and liveness probes
- resource requests and limits
- Horizontal Pod Autoscalers
- Traefik or nginx ingress
- a local PostgreSQL database deployment
- service accounts
- basic NetworkPolicy ingress controls

## Replace Before Applying

Update these placeholder values:

- image names in `backend-deployment.yaml` and `frontend-deployment.yaml` after CI pushes to a registry
- `autohealops.local` in `ingress.yaml` and `configmap.yaml` if you use a different local hostname
- `ingressClassName` in `ingress.yaml` if your cluster uses a different ingress controller
- database credentials in a real Secret created from `secret.example.yaml`

## Required Local Add-ons

Install these before applying all manifests:

- an ingress controller such as Traefik or nginx
- metrics-server for HPA

## Apply

```bash
kubectl apply -f k8s/
```

For real deployments, copy `secret.example.yaml` to a local untracked file, replace values, and apply that file instead.

## Verify

```bash
kubectl -n autohealops get pods
kubectl -n autohealops get svc
kubectl -n autohealops get ingress
kubectl -n autohealops get hpa
```

For a local k3d cluster with port `8081` mapped to the ingress load balancer, add this to `/etc/hosts`:

```text
127.0.0.1 autohealops.local
```

Then open:

```text
http://autohealops.local:8081
```

## Delete

```bash
kubectl delete -f k8s/ --ignore-not-found
```
