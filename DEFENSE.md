# Defense runbook

Everything needed to bring the system up on a machine that is not the one it was written on, drive
the demo, and answer for the decisions. The long-form reasoning behind every choice is in
[`ROADMAP.md`](ROADMAP.md); this file is the short version you can follow while someone watches.

## What is actually graded

30 points for the code, +15 for Kubernetes, +15 for the blockchain, capped at 60 —
and the total is **multiplied by the share of tests still passing after the live
modification**. The modification is a precondition: without it there are no points at
all. So the order of priorities on the day is: bring the system up, do the modification,
and above all do not break the nine endpoints that already work.
[`MODIFIKACIJE.md`](MODIFIKACIJE.md) is the playbook for that half.

Three rules the assistants enforce, all of which this project already satisfies:

- `/report` must go through the MongoDB aggregation framework. Ours is
  `$unwind → $group → $sort → $project`.
- Raw SQL is not allowed, it has to be the ORM. `authentication.py` never builds a
  SQL string.
- Filter in the query, not in a Python loop. The single legitimate exception is Redis,
  which has no query language — say that out loud before you are asked.

**Verified at 179/179 (100%) on the official `iep_grader`**, every level including the
blockchain one, against a stack built from scratch by `pokreni.sh`.

## 0. Before you sit down

On the faculty machine, in this order. The first two are the ones that hurt if you skip them.

```bash
# 1. Pull the four public images while you still have time to notice a slow network.
docker pull mysql && docker pull mongo && docker pull redis
docker pull trufflesuite/ganache-cli && docker pull busybox:1.36

# 2. Build your four.
git clone https://github.com/St1viG/IEP.git && cd IEP
docker compose -f deploy/deployment.yaml build

# 3. Confirm Kubernetes is up and which flavour it is.
kubectl config current-context
kubectl get nodes
```

`docker compose build` installs pinned dependencies, so it needs the network once and then never
again. It takes a few minutes; the four images share one cached pip layer.

## 1. Bring the system up

```bash
sh pokreni-k8s.sh                 # Windows: pokreni-k8s.cmd
```

That builds, loads the images into the cluster, applies the manifest, waits on every
deployment and the migration Job, and opens the port-forwards. The steps by hand:

```bash
docker compose -f deploy/deployment.yaml build
sh deploy/load-images.sh          # puts the four local images in the cluster's own store
kubectl apply -f deploy/k8s.yaml
kubectl get pods -w               # wait for Running; the migration job goes to Completed
```

`load-images.sh` is not optional. `k8s.yaml` pins your four images to `imagePullPolicy: Never`, so
the node has to already hold them — building with Docker is not enough, because the cluster keeps a
separate image store. The script detects minikube, kind, k3d and Docker Desktop and does the right
thing for each. If it prints `unrecognised context`, tell it which cluster you are on and load by hand.

Expected steady state:

```
mysql-…            1/1  Running
mongo-…            1/1  Running
redis-…            1/1  Running
ganache-…          1/1  Running
migration-job-…    0/1  Completed
authentication-…   1/1  Running
employee-…         1/1  Running   ×3
director-…         1/1  Running
```

### Reaching the services

The three web services are `NodePort` on 30000 / 30001 / 30002. On minikube, `minikube ip` gives you
the host. On Docker Desktop and kind those ports are **not** published on the host, so use
port-forwards instead — this still goes through Service → Deployment → pod, so the three employee
replicas are genuinely being load balanced:

```bash
kubectl port-forward service/authentication-service 5000:5000 &
kubectl port-forward service/employee-service       5001:5000 &
kubectl port-forward service/director-service       5002:5000 &
kubectl port-forward service/ganache-service        8545:8545 &     # only for scenario.py
```

### If something is wrong

| Symptom | Cause | Fix |
|---|---|---|
| `ErrImageNeverPull` | image not in the node's store | run `deploy/load-images.sh` |
| `ImagePullBackOff` on mysql/mongo/redis/ganache | no network for a first pull | `docker pull` it, then delete the pod |
| migration job `Completed` but nobody can log in | job ran against a wiped volume and will not re-run | `kubectl delete job migration-job && kubectl apply -f deploy/k8s.yaml` |
| MongoDB pod restarts, `/search` hangs 30s, `/report` 500s while `/pending_orders` is fine | a mongo 8 image; it refuses to start on kernel 6.19+ (SERVER-121912). The 30s is PyMongo's server-selection timeout | the manifests pin `mongo:7`; check nothing has overridden it |
| ganache pod slow to be ready | the image is amd64 only, emulated on Apple Silicon | wait 30 s; on an x86 faculty machine it is instant |
| CoreDNS `CrashLoopBackOff`, pods exit 139 | the cluster was created while the disk was full and its state is corrupt | `docker desktop kubernetes reset-cluster`, then load the images and apply again |
| `read-only file system` while loading images | Docker's VM is out of disk, so it remounted read-only | free space on the **host**, restart Docker, then `docker builder prune -af` |

Keep an eye on free disk. Docker's VM goes read-only when the host fills up, and the failures it
then produces (`read-only file system`, a segfaulting CoreDNS) point nowhere near the real cause.

### Verified

This exact path was run end to end on Docker Desktop Kubernetes v1.36.1: images loaded with
`load-images.sh`, `kubectl apply`, migration Job Completed in 45 s, all ten pods Running,
`scenario.py` green through port-forwards, the MySQL pod deleted and login working again with no
service restart, the Mongo pod deleted and `/report` still correct, and `employee` at 3/3.

## 2. The demo

Compose, if Kubernetes is not the thing being shown:

```bash
sh pokreni.sh                     # Windows: pokreni.cmd
sh deploy/proveri.sh director /report      # one route, with a token, no curl
```

The fastest, safest version is the script — it drives every endpoint and a full three-voter ballot,
and prints an `ok` line per step:

```bash
python scenario.py
```

Run it by hand instead if the examiner wants to see the parts. `$T` is the token from each login.

```bash
# The director the migration job seeded.
curl -s localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"onlymoney@gmail.com","password":"evenmoremoney"}'

# An employee registers and logs in.
curl -s localhost:5000/register -H 'Content-Type: application/json' \
  -d '{"forename":"Donald","surname":"Duck","email":"donald@duck.com","password":"quackquack"}'

# The employee proposes a purchase.
curl -s localhost:5001/create_buy_order -H "Authorization: Bearer $EMPLOYEE" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ferrari F40","categories":["vehicles","luxury"],"buying_price":500000,
       "info":{"engine":{"power":350}}}'

# The director sees it waiting, and opens a vote on it.
curl -s localhost:5002/pending_orders -H "Authorization: Bearer $DIRECTOR"
curl -s localhost:5002/decision -H "Authorization: Bearer $DIRECTOR" \
  -H 'Content-Type: application/json' \
  -d '{"uuid":"<uuid>","voters":["0x…","0x…","0x…"]}'
```

Then cast two of the three ballots from ganache accounts and show the asset appear in `/search` and
`/report` **without calling the director again** — that is the point of the whole voting section.

Worth showing, in this order, because each one answers a requirement:

1. **Three replicas.** `kubectl get pods -l app=employee` → three.
2. **Persistence.** `kubectl delete pod -l app=mysql`, wait for the new pod, then log in again with
   no restart of anything. The data survived the pod, and the service survived the address change.
   Same for `-l app=mongo`: `/search` still returns the asset.
3. **Rejection.** Propose something, open a vote, cast two rejects, and show it gone from
   `/pending_orders` and absent from `/search`.
4. **Validation order.** `{"forename":"","email":"bad"}` to `/register` gives
   `"Field forename is missing."`, not `"Invalid email."`

## 3. Questions to have an answer for

**Why does an unsold asset still count in `spent`?**
The spec defines `spent` with no condition on it — "ukupan iznos potrošen za kupovinu imovine koja
pripada datoj kategoriji" — and the restricting sentence names only "obračun zarade", the earnings.
So an asset the fund still holds contributes what was paid for it and earns nothing. It is also why
the sort has a `spent` tiebreak at all: with unsold categories in the report, many rows tie at
`earned: 0`. The `$match` for the other reading is one line and is noted in `ROADMAP.md` §4.2.

**Why do the returned transactions carry no `from` or `nonce`?**
Because the sender is not known when the contract is deployed. Any of the allowed voters may cast
either ballot, and a nonce is per-account. So `/decision` returns `to`, `data`, `gas`, `gasPrice` and
`chainId`, and the voter supplies the rest. The course reference bakes in `from` and `nonce` because
there it is one known customer paying one known invoice.

**How does an approved order reach MongoDB if nobody calls the service?**
The employees vote at a moment the director takes no part in. `/decision` records `uuid → contract
address` in a Redis hash, and a background thread in the director polls each live contract's
`status()` once a second. On conclusion it claims the contract with `HDEL` — which returns the number
of fields it removed, so exactly one caller can win — then writes the asset and retires the order.
The two director read endpoints settle before they answer as well, so `/report` is never stale. This
is the same shape the course uses in `docs/materials/Docker/JWT_ban/user.py`, which starts a Redis
listener thread before `application.run`.

**Why is the director one replica?**
Only so there is one poller. The claim is atomic, so a second one would be correct rather than
harmful, but there is nothing to gain: the director serves one person. The employee service, which
serves everyone, is the one the spec asks to scale, and it is at three.

**Why does Redis have no PersistentVolume?**
The spec calls it "Redis servis koji se koristi za čuvanje privremenih informacija". Orders live
there only between being proposed and being voted on. The two databases that hold durable state,
MySQL and MongoDB, both have a PV and a PVC with `persistentVolumeReclaimPolicy: Retain`.

**Why `--evm-version istanbul` when compiling the contract?**
The assignment mandates the `trufflesuite/ganache-cli` image, which is ganache 6 and predates the
`PUSH0` opcode that current `solc` emits by default. Deploying that bytecode fails with a bare
"invalid opcode" that names nothing.

**Isn't `$unwind` double counting?**
No, it is the spec's own rule: "Ukoliko jedna imovina pripada većem broju kategorija, ona se računa u
statistiku svake od tih kategorija." One document becomes N, each contributing its full price to a
different category's group.

**Why does the migration Job have an initContainer?**
Measured, not theoretical. With the course's `backoffLimit: 4` alone, the job failed three times and
only succeeded on the fourth attempt 86 seconds in, because MySQL needs about a minute to initialise
an empty data directory. One slower disk and the seeded director never exists. The initContainer
blocks on `nc -z mysql-service 3306` and the job then completes in 18 seconds.

**Why is the code not written in the course's style?**
The spec dictates the libraries, the error strings, the response fields and the deployment artifacts.
It says nothing about formatting, so that follows PEP 8, enforced by `ruff` and `pre-commit`.
`decorators.py` is the one file kept as the course wrote it, because `role_check` is course API.

## 4. Fallbacks

- **Kubernetes will not come up.** `docker compose -f deploy/deployment.yaml up -d` gives the same
  system on 5000/5001/5002, and `scenario.py` runs against it unchanged.
- **A rebuild fails on the day.** Every dependency is pinned in `requirements.txt`; if pip still
  cannot resolve, the images from the night before are already in the local Docker store — skip the
  build step and go straight to `load-images.sh`.
- **Port 5000 is taken** (AirPlay Receiver on macOS answers with an empty 403):
  `AUTHENTICATION_PORT=5100 EMPLOYEE_PORT=5101 DIRECTOR_PORT=5102 docker compose …` and point
  `scenario.py` at them with the matching `*_URL` variables.
