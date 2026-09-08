# Database Replication Example

Demonstrates PostgreSQL **streaming replication** on Kubernetes using StatefulSets to optimize read throughput.

## The Problem

A single database instance handles every query. Under concurrent read load it becomes a bottleneck — the only way to scale is to use a bigger machine (vertical scaling), which has hard limits and is expensive.

## The Solution

**Primary–Replica streaming replication.**

```
         Writes                     Reads (load-balanced)
    ┌────────────┐            ┌───────────────────────────┐
    │            │            │                           │
    ▼            │            ▼           ▼           ▼
┌─────────┐      │    ┌─────────────┐ ┌─────────────┐ ┌─── ...
│ Primary │ ─WAL─┤──► │  Replica 0  │ │  Replica 1  │ │
│  (r/w)  │      │    │  (read only)│ │  (read only)│ │
└─────────┘      │    └─────────────┘ └─────────────┘ └─── ...
     ▲            │            ▲
     │            │            │
postgres-write    │      postgres-read  (K8s round-robins across all replicas)
  (Service)       │         (Service)
```

- **`postgres-write` service** → primary pod only (all writes)
- **`postgres-read` service** → all replica pods, Kubernetes load-balances
- Each replica is a live hot-standby: WAL changes from the primary propagate in real time
- Add more replicas to scale reads horizontally without touching the primary

## Architecture

| Resource | Kind | Purpose |
|---|---|---|
| `postgres-primary` | StatefulSet (1 pod) | Accepts writes, streams WAL to replicas |
| `postgres-replica` | StatefulSet (2 pods) | Read-only hot-standbys |
| `postgres-primary-headless` | Service (headless) | Stable DNS for replica clone step |
| `postgres-replica-headless` | Service (headless) | Stable DNS per replica pod |
| `postgres-write` | Service (ClusterIP) | Write endpoint for applications |
| `postgres-read` | Service (ClusterIP) | Read endpoint, load-balanced |

## Demo: Before vs After

### Before — single instance

```bash
# Deploy a single PostgreSQL instance
kubectl apply -f demo/before/single-db.yaml

# Wait for the pod to be ready
kubectl rollout status statefulset/postgres -n db-before

# Seed test data
kubectl apply -f demo/before/load-test.yaml
# Wait for seed-data job, then run read-benchmark job
kubectl wait --for=condition=complete job/seed-data -n db-before --timeout=120s
kubectl apply -f demo/before/load-test.yaml   # re-apply to trigger read-benchmark

# Watch results
kubectl logs -f job/read-benchmark -n db-before
```

**Expected output** — all 20 clients queue on the single instance:
```
transaction type: <builtin: select only>
scaling factor: 20
clients: 20 / threads: 4 / duration: 60s

tps = ~800   (one instance, all clients competing)
```

---

### After — primary + 2 replicas

```bash
# Deploy namespace, config, secret, primary, replicas, and services
kubectl apply -f demo/after/replication.yaml

# Wait for primary to be fully ready before replicas clone it
kubectl rollout status statefulset/postgres-primary -n db-replication

# Wait for both replicas to finish cloning and start
kubectl rollout status statefulset/postgres-replica -n db-replication

# Seed data on primary (replicas receive it via WAL)
kubectl apply -f demo/after/load-test.yaml
kubectl wait --for=condition=complete job/seed-data -n db-replication --timeout=120s

# Verify replication is healthy
kubectl logs -f job/verify-replication -n db-replication
# Expected: primary confirmed, replicas confirmed, replication lag near zero

# Run the read benchmark against the read service
kubectl logs -f job/read-benchmark -n db-replication
```

**Expected output** — reads distributed across 2 replicas:
```
transaction type: <builtin: select only>
scaling factor: 20
clients: 20 / threads: 4 / duration: 60s

tps = ~1600  (2 replicas share the load — roughly 2× improvement)
```

---

## Scaling reads further

```bash
# Add a third replica — zero downtime, primary unaffected
kubectl scale statefulset postgres-replica --replicas=3 -n db-replication

# The new pod clones the primary automatically and joins the read pool
kubectl rollout status statefulset/postgres-replica -n db-replication
```

Each additional replica adds another fraction of read capacity. The `postgres-read` service picks up new pods automatically via label selector.

## Verifying replication status

```bash
# Check WAL sender connections on the primary
kubectl exec -n db-replication postgres-primary-0 -- \
  psql -U app appdb -c "SELECT client_addr, state, sync_state FROM pg_stat_replication;"

# Check each replica is in recovery (read-only standby) mode
kubectl exec -n db-replication postgres-replica-0 -- \
  psql -U app appdb -c "SELECT pg_is_in_recovery();"

# Check replication lag (should be near zero under normal conditions)
kubectl exec -n db-replication postgres-primary-0 -- \
  psql -U app appdb -c "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag FROM pg_stat_replication LIMIT 1;"
```

## Cleanup

```bash
kubectl delete namespace db-before
kubectl delete namespace db-replication
```

## Key Kubernetes concepts used

| Concept | Why |
|---|---|
| **StatefulSet** | Each pod gets a stable hostname and its own PVC — essential for databases |
| **Headless Service** | Gives each pod a predictable DNS name so replicas can find the primary |
| **volumeClaimTemplates** | Each pod gets its own persistent storage automatically |
| **Init Container** | Runs `pg_basebackup` to clone the primary before the replica starts |
| **Label selectors on Services** | `role: primary` and `role: replica` labels cleanly route traffic to the right pods |
| **fsGroup (securityContext)** | Ensures mounted PVCs are owned by the `postgres` OS group |
