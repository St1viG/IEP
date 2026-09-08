# CronJob example

This example runs a small scheduled task every minute.

Apply:

```bash
kubectl apply -f cronjob.yaml
```

Watch CronJob and Jobs:

```bash
kubectl get cronjob
kubectl get jobs -w
```

After a Job appears, inspect its Pod logs:

```bash
kubectl get pods
kubectl logs <pod-name>
```

You should see output like:

```text
CronJob started at ...
This simulates a scheduled cleanup, backup, or report task.
```

Manually trigger a Job from the CronJob:

```bash
kubectl create job manual-timestamp-logger --from=cronjob/timestamp-logger
```

Cleanup:

```bash
kubectl delete -f cronjob.yaml
kubectl delete job manual-timestamp-logger
```
