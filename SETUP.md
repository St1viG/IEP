# Setup and running

Three ways to run this, in increasing order of what they prove:

1. **Docker Compose** — the whole system in containers, one command. Use this for everyday work.
2. **Kubernetes** — what the assignment actually grades.
3. **On the host** — Flask processes on your machine against containerised databases. Fastest edit
   loop, only needed if you want a debugger.

Everything below assumes the repository root as the working directory.

## What you need

**Docker, and nothing else.** Python on the host is optional: the tests and the scenario both have
container wrappers. On Windows use PowerShell or `cmd`; every script has a `.cmd` twin.

```
docker --version
docker compose version
kubectl version --client      # only for the Kubernetes path
```

If `docker info` fails, Docker Desktop is not running. On the faculty machines Docker Desktop is
installed but you may need the invigilator to grant your account Docker privileges — ask as soon as
you sit down.

---

## 1. Docker Compose

```cmd
pokreni.cmd
```

```sh
sh pokreni.sh
```

That wipes any previous state, builds the four images, starts everything, waits until the services
answer, and prints where they are listening. The first build takes a few minutes because it installs
the pinned dependencies; every build after that is seconds.

| | URL |
|---|---|
| authentication | http://localhost:5000 |
| employee | http://localhost:5001 |
| director | http://localhost:5002 |
| ganache | http://localhost:8545 |
| adminer (browse MySQL) | http://localhost:8080 |

**On macOS port 5000 is taken by AirPlay Receiver**, which answers every request with an empty `403`.
Move the ports:

```sh
AUTHENTICATION_PORT=5100 EMPLOYEE_PORT=5101 DIRECTOR_PORT=5102 sh pokreni.sh
```

Windows does not have this problem, so the defaults are right on the defense machine.

### Poke a single route

No curl, no local Python — it runs inside one of the project's own images and handles the login for
you.

```cmd
deploy\proveri.cmd director /report
deploy\proveri.cmd director /pending_orders
deploy\proveri.cmd employee /search name=Ferrari
```

```sh
sh deploy/proveri.sh director /report
sh deploy/proveri.sh employee /search name=Ferrari
```

A body is given as `key=value` pairs, which needs no quoting on either shell — this matters on
Windows, where `cmd` does not honour `\"` escapes, so a JSON string typed the Unix way arrives
mangled. Values that parse as JSON are sent as JSON, so `selling_price=200` is a number and
`approved=true` is a boolean. A whole JSON object still works where you need nesting, and is easiest
to quote from `sh`:

```sh
sh deploy/proveri.sh employee /search '{"info_filters": [{"field": "engine.power", "operator": "gt", "value": 100}]}'
```

If you moved the ports, tell it:

```sh
DIRECTOR_URL=http://host.docker.internal:5102 sh deploy/proveri.sh director /report
```

### Stop it

```
docker compose -f deploy/deployment.yaml down        # keep the data
docker compose -f deploy/deployment.yaml down -v     # wipe the data too
```

---

## 2. Kubernetes

```cmd
pokreni-k8s.cmd
```

```sh
sh pokreni-k8s.sh
```

One command: build, load the images into the cluster, apply the manifest, wait for every deployment
and the migration Job, and open the port-forwards. Enable Kubernetes first in
**Docker Desktop → Settings → Kubernetes → Enable Kubernetes**, and wait for the indicator to go
green — the first enable takes several minutes.

By hand, which is what the script does:

```
docker compose -f deploy/deployment.yaml build
deploy\load-images.cmd                 # sh deploy/load-images.sh
kubectl apply -f deploy/k8s.yaml
kubectl get pods -w
```

**`load-images` is not optional.** `k8s.yaml` uses `imagePullPolicy: Never` for the four images you
build, and the cluster keeps an image store of its own that cannot see the Docker daemon's. Building
is not enough. The script detects minikube, kind, k3d and Docker Desktop and does the right thing for
each.

Everything healthy looks like this:

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

`NodePort` 30000 (authentication), 30001 (employee), 30002 (director), 30003 (ganache). On minikube
that is `minikube ip` on those ports. **Docker Desktop and kind do not publish NodePorts on the
host**, so use port-forwards — `pokreni-k8s` opens them for you:

```
kubectl port-forward service/authentication-service 5000:5000
kubectl port-forward service/employee-service       5001:5000
kubectl port-forward service/director-service       5002:5000
kubectl port-forward service/ganache-service        8545:8545
```

This still goes Service → Deployment → pod, so the three employee replicas are genuinely being load
balanced.

### Tear down

```
kubectl delete -f deploy/k8s.yaml
```

---

## 3. On the host

Only the databases in containers; the three services as Flask processes you can attach a debugger to.

```sh
python -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

docker compose -f deploy/development.yaml up -d    # MySQL, MongoDB, Redis, ganache, adminer
python src/migrate.py                              # create the tables, seed the director

PORT=5000 python src/authentication.py
PORT=5001 python src/employee.py
PORT=5002 python src/director.py
```

Each service reads its settings from the environment and falls back to `localhost`, so nothing needs
configuring for this to work.

---

## Running the tests

174 tests. The integration ones need `deploy/development.yaml` up — the databases must be published
on the host, which `deployment.yaml` deliberately does not do.

### In a container, no Python needed

```cmd
docker compose -f deploy/development.yaml up -d
testovi.cmd
```

```sh
docker compose -f deploy/development.yaml up -d
sh testovi.sh
```

Anything you pass is handed to pytest:

```sh
sh testovi.sh -m "not integration"    # the 33 that need no services at all
sh testovi.sh -k report -v            # one file's worth, verbosely
sh testovi.sh -x                      # stop at the first failure
```

### With Python on the host

```sh
python -m pytest                      # everything
python -m pytest -m "not integration" # no services needed
python -m pytest -k voting -v
```

A green run looks like this:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/stevangnjato/Desktop/programming/etf/IEP
configfile: pytest.ini
testpaths: tests
plugins: timeout-2.4.0
timeout: 15.0s
collected 174 items

tests/test_authentication.py ...............................       [ 17%]
tests/test_configuration.py .......                                [ 21%]
tests/test_employee_search.py ...................                  [ 32%]
tests/test_infrastructure.py ...                                   [ 34%]
tests/test_models.py ....                                          [ 36%]
tests/test_orders.py ...........................................   [ 61%]
tests/test_report.py .........                                     [ 66%]
tests/test_validation.py ..........................                [ 81%]
tests/test_voting.py ................................              [100%]

============================= 174 passed in 26.22s =============================
```

**Watch the skip count.** If the services are not reachable the run still exits green, as
`33 passed, 141 skipped` — pytest skips rather than fails so that a laptop with nothing running can
still check the pure unit tests. A run that proves anything says **174 passed** and mentions no skips.

Every test has a 15 second timeout, so a service that accepts connections but never answers fails the
run instead of hanging it.

### End to end

`scenario.py` walks all nine endpoints including a full three-voter ballot, and tags each run so it
can be replayed against a live system without resetting anything.

```sh
python scenario.py                                        # localhost:5000/5001/5002
AUTHENTICATION_URL=http://localhost:5100 \
EMPLOYEE_URL=http://localhost:5101 \
DIRECTOR_URL=http://localhost:5102 python scenario.py
```

---

## Rebuilding after a change

Rebuild only the service you touched. It takes seconds, because the dependency layer is cached and
shared by all four images.

```
docker compose -f deploy/deployment.yaml up -d --build director
```

`employee`, `authentication` or `migration` instead of `director`, depending on where the change was.
If you changed `models.py`, the migration has to run again against an empty database, so
`down -v` first.

---

## Verifying it on Windows

The scripts were written on macOS and every `.sh` has been run there; the `.cmd` twins have not,
because there is no Windows here. Run this once on the machine you will defend on, in order. It takes
about twenty minutes, almost all of it the first build, and it exercises every path you will use.

```cmd
docker info                                     :: must succeed, else Docker Desktop is not running

pokreni.cmd                                     :: build + start, prints the URLs
deploy\proveri.cmd director /report              :: -> {"statistics": []}
deploy\proveri.cmd director /pending_orders      :: -> {"orders": []}
deploy\proveri.cmd employee /search name=x       :: -> {"assets": []}

docker compose -f deploy/deployment.yaml down
docker compose -f deploy/development.yaml up -d
testovi.cmd                                     :: -> 174 passed, and no skips

docker compose -f deploy/development.yaml down
pokreni-k8s.cmd                                 :: enable Kubernetes in Docker Desktop first
kubectl get pods                                :: 3 employee pods, migration-job Completed
deploy\proveri.cmd director /report              :: through the port-forwards
kubectl delete -f deploy/k8s.yaml
```

Things that differ on Windows and are worth watching for:

- **Port 5000 is free**, so the defaults are correct — no `AUTHENTICATION_PORT` juggling.
- `cmd` does not honour `\"` inside quotes, which is why request bodies are `key=value`.
- Docker Desktop's Kubernetes is the same kind-based cluster as on macOS, so
  `deploy\load-images.cmd` takes the `desktop-control-plane` path and NodePorts still are not
  published on the host.
- If a `.cmd` misbehaves, the `.sh` next to it is the reference for what it should do, and Git Bash
  will run it unchanged.

## When something is wrong

| Symptom | Cause | Fix |
|---|---|---|
| `bind: address already in use` on 5000 | AirPlay Receiver, macOS only | move the ports, see above |
| `ErrImageNeverPull` | the image is not in the cluster's store | `deploy/load-images.cmd` |
| `ImagePullBackOff` on mysql/mongo/redis/ganache | no network for a first pull | `docker pull` it, then delete the pod |
| `/search` hangs ~30s, `/report` 500s, `/pending_orders` fine | MongoDB is unreachable; 30s is PyMongo's server-selection timeout | check the mongo pod; the manifests pin `mongo:7` because 8.x will not start on kernel 6.19+ |
| migration Job `Completed` but nobody can log in | the Job ran against a volume that was later wiped, and a completed Job does not re-run | `kubectl delete job migration-job` and apply again |
| CoreDNS `CrashLoopBackOff`, pods exit 139 | the cluster was created while the disk was full | free space, then `docker desktop kubernetes reset-cluster` |
| `read-only file system` anywhere in Docker | Docker's VM is out of disk | free space on the **host**, restart Docker, `docker builder prune -af` |
| tests skip instead of running | the development stack is not up, or a host MySQL/MongoDB is shadowing a container on the same port | `docker compose -f deploy/development.yaml up -d`; check `lsof -i:27017` |
| pytest: `unrecognized arguments` when running the grader | a leftover `grade_report.json` confuses pytest's rootdir | delete it and rerun |

Keep an eye on free disk. When the host fills up, Docker's VM remounts read-only and the errors it
then produces point nowhere near the real cause.
