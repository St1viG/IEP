# NetworkPolicy example

This example creates:

- one `web` Deployment and Service
- one `allowed-client` Pod
- one `blocked-client` Pod
- one `NetworkPolicy`

The policy allows traffic to the `web` Pods only from Pods with:

```yaml
access: allowed
```

Apply:

```bash
kubectl apply -f network-policy-example.yaml
```

Test the allowed client:

```bash
kubectl exec -n network-policy-demo allowed-client -- curl -m 3 http://web
```

Test the blocked client:

```bash
kubectl exec -n network-policy-demo blocked-client -- curl -m 3 http://web
```

The first command should return the nginx page.
The second command should timeout.

Cleanup:

```bash
kubectl delete namespace network-policy-demo
```

## CNI requirement

NetworkPolicy enforcement depends entirely on the CNI plugin — Kubernetes only stores the object, the CNI enforces it. Clusters whose CNI does not support NetworkPolicy will **silently accept the policy but never block any traffic**.

| Environment | CNI | Enforces NetworkPolicy? |
|---|---|---|
| Docker Desktop | kindnet | **No** |
| Minikube (default) | kindnet | **No** |
| Minikube + Calico | Calico | Yes |
| kind (default) | kindnet | **No** |
| kind + Calico/Cilium | Calico or Cilium | Yes |
| GKE, EKS, AKS | varies (usually Calico-based) | Yes |

### Testing this example locally with enforcement

Use minikube with Calico:

```bash
minikube start --cni=calico
# wait ~60s for Calico pods to become ready
kubectl get pods -n kube-system | grep calico

kubectl apply -f network-policy-example.yaml
```

Then re-run the curl tests — `allowed-client` succeeds, `blocked-client` times out.
