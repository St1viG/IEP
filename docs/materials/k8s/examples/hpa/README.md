# HPA example

This example demonstrates a `HorizontalPodAutoscaler`.

The HPA watches CPU usage for the `php-apache` Deployment and changes the number of replicas between 1 and 10.

Apply the workload and HPA:

```bash
kubectl apply -f hpa-example.yaml
kubectl get deployment php-apache
kubectl get hpa php-apache
```

The HPA needs metrics from the Kubernetes Metrics Server.

For Minikube:

```bash
minikube addons enable metrics-server
```

For Docker Desktop Kubernetes, install Metrics Server:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Docker Desktop may need Metrics Server to allow insecure kubelet TLS. If metrics do not appear, edit the Metrics Server Deployment and add this argument:

```text
--kubelet-insecure-tls
```

This has already been done and the changed Metrics Server can be started witht the following command:

```bash
kubectl apply -f components.yaml
```

Check whether metrics are available:

```bash
kubectl top pods
kubectl top nodes
```

Generate load:

```bash
kubectl apply -f load-generator.yaml
```

Watch scaling:

```bash
kubectl get hpa php-apache -w
kubectl get pods -l app=php-apache -w
```

Stop the load:

```bash
kubectl delete -f load-generator.yaml
```

Cleanup:

```bash
kubectl delete -f hpa-example.yaml
```
