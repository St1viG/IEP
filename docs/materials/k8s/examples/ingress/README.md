# Ingress example

This example creates two Deployments, two internal Services, and one Ingress.

The Ingress routes:

```text
http://web.local/    -> web-v1 Service
http://web.local/v2  -> web-v2 Service
```

Ingress requires an Ingress Controller.

Docker Desktop Kubernetes does not include an Ingress Controller by default.
Install the NGINX Ingress Controller:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.1/deploy/static/provider/cloud/deploy.yaml
```

Wait until the controller Pod is running:

```bash
kubectl get pods -n ingress-nginx
kubectl get service -n ingress-nginx
```

Then add this line to your hosts file:

```text
127.0.0.1 web.local
```

## Apply the example

```bash
kubectl apply -f ingress-example.yaml
kubectl get pods
kubectl get services
kubectl get ingress
```

Test:

```bash
curl http://web.local/
curl http://web.local/v2
```

Cleanup:

```bash
kubectl delete -f ingress-example.yaml
```
