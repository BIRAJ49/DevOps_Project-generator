# AutoHealOps Local Kubernetes Manifests

These manifests deploy AutoHealOps to a local Kubernetes cluster such as `k3d`, `kind`, or local K3s with:

- ConfigMap and Secret-based configuration
- readiness and liveness probes
- resource requests and limits
- Horizontal Pod Autoscalers
- nginx ingress

## Replace Before Applying

Update these placeholder values:

- image names in `backend-deployment.yaml` and `frontend-deployment.yaml` after CI pushes to a registry
- `autohealops.local` in `ingress.yaml` and `configmap.yaml` if you use a different local hostname
- database credentials in a real Secret created from `secret.example.yaml`

## Required Local Add-ons

Install these before applying all manifests:

- nginx ingress controller
- metrics-server for HPA

## Apply Order

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.example.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

For real deployments, copy `secret.example.yaml` to a local untracked file, replace values, and apply that file instead.

## Delete Order

```bash
kubectl delete -f k8s/ingress.yaml --ignore-not-found
kubectl delete -f k8s/hpa.yaml --ignore-not-found
kubectl delete -f k8s/frontend-deployment.yaml --ignore-not-found
kubectl delete -f k8s/backend-deployment.yaml --ignore-not-found
kubectl delete -f k8s/frontend-service.yaml --ignore-not-found
kubectl delete -f k8s/backend-service.yaml --ignore-not-found
kubectl delete -f k8s/secret.example.yaml --ignore-not-found
kubectl delete -f k8s/configmap.yaml --ignore-not-found
kubectl delete -f k8s/namespace.yaml --ignore-not-found
```
