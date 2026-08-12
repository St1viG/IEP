# Roadmap: Sistem za upravljanje investicionim fondom

Implementation plan for [`docs/Projekat/IEP_Projekat_2026.md`](docs/Projekat/IEP_Projekat_2026.md).

Code lives at the repo root, where this file sits. `docs/Projekat/` holds only the spec, `docs/materials/` the course examples. All paths below are relative to the root. Tick the checkboxes as you ship each piece.

## Principles

1. **Validation order is graded.** Every endpoint spec ends with "Odgovarajuće provere se vrše u navedenom redosledu." Wrong order means wrong error string for a request that violates two rules at once. Write the checks top to bottom in the listed order, and return on the first failure.
2. **Exact strings.** Error messages are literal, including the trailing period. `"Invalid buying price."` not `"Invalid buying price"`.
3. **Push work into the query.** The spec says to use SQLAlchemy and PyMongo "u što većoj meri". Filtering an in-memory list in Python where a Mongo query would do is a deduction.
4. **`401 Missing Authorization Header` is free.** That JSON body is `flask_jwt_extended`'s default response for a missing header. Do not override it, just use `@jwt_required()`.
5. **Build in the order below.** Each section leaves you with a system you can demo. Do not start Kubernetes before the app works under Compose, and do not start the blockchain before `/decision` works without it.

## Target layout

```
IEP/
  configuration.py          # env vars, one Configuration class per concern
  models.py                 # SQLAlchemy: User, Role, UserRole
  validation.py             # shared ordered-check helpers
  decorators.py             # role_check, shared by employee.py and director.py
  authentication.py         # register / login / delete
  employee.py               # search / create_buy_order / create_sell_order
  director.py               # pending_orders / decision / report
  migrate.py                # create_all + seed director (runs as a k8s Job)
  utilities.py              # web3 helpers (section 6)
  voting.sol                # (section 6)
  output/Voting.abi|.bin    # (section 6, committed like the course examples)
  *.dockerfile              # one per service, plus one for migration
  development.yaml          # infra only, Flask runs on host
  deployment.yaml           # everything in containers
  k8s.yaml                  # the graded Kubernetes file
  scenario.py               # end-to-end exercise of every endpoint
  tests/                    # pytest, `-m "not integration"` skips the ones needing containers
  pytest.ini                # pythonpath = . so tests import the services directly
  requirements.txt          # what the images install
  requirements-dev.txt      # the above plus pytest
  venv/                     # gitignored
  docs/Projekat/            # the spec, not code
  docs/materials/           # course examples to crib from
```

No formatter and no pre-commit hook here on purpose: the course house style (`timedelta ( hours = 1 )`, aligned ternaries) is what the examples and the professor read, and `black` or `ruff format` would rewrite all of it.

## How the tests reach the services

Each service builds its Flask app, its Mongo handle and its Redis handle at **import time**, straight off `Configuration`. So a test that wants a service pointed somewhere else patches `Configuration` first and then `importlib.reload`s the service module. `conftest.py` does exactly that: `_test` suffixes on the MySQL database, the Mongo database and the Redis orders hash, so a test run never touches what `development.yaml` is serving to `scenario.py`.

**Never hold a module-level reference to the `Configuration` class in test code.** `test_configuration.py` reloads the `configuration` module to check the env-var branches, and every reload binds a **new class object** to `configuration.Configuration`. Anything holding the old one (a `from configuration import Configuration` executed earlier, which is every already-imported module) keeps patching a class nobody reads any more. The failure is silent and nasty: the fixture patches the orphan, the reloaded service reads the live values, and the test suite runs against the development database. It wiped the assets `scenario.py` had just created before this was caught. Two guards now: `test_configuration.py` restores the original class object when it is done, and `conftest.py` resolves `configuration.Configuration` at call time instead of importing the name.

---

## Section 1: Authentication service

Everything downstream reads the JWT claims this service issues, so its shape has to be settled first.

### 1.1 Project setup

- [x] `python -m venv venv && source venv/bin/activate`
- [x] `requirements.txt`: start from [`docs/materials/Ispit/EtherBank/requirements.txt`](docs/materials/Ispit/EtherBank/requirements.txt) and add `pymongo`, `redis`. Drop `web3` until section 6.
- [x] `development.yaml` with MySQL (3306), adminer (8080), mongo (27017), redis (6379). Crib the MySQL/adminer block from [`docs/materials/Ispit/EtherBank/development.yaml`](docs/materials/Ispit/EtherBank/development.yaml) and the mongo block from [`docs/materials/mongodb/mongo.yaml`](docs/materials/mongodb/mongo.yaml).
- [x] `configuration.py` following [`docs/materials/Ispit/EtherBank/configuration.py`](docs/materials/Ispit/EtherBank/configuration.py): env var with a localhost fallback for every setting. Add `MONGO_*` and `REDIS_*` now so you do not touch it again later.

**Gotcha:** EtherBank's `configuration.py:9` has a copy-paste bug, it tests `"DATABASE_NAME" in os.environ` when reading `BLOCKCHAIN_URL`. Do not inherit it.

**Gotcha:** `DATABASE_URL` falls back to `127.0.0.1`, not `localhost`. `mysqlclient` reads the literal host `localhost` as "use the unix socket" and ignores TCP entirely, so it either misses the container or hits a locally installed MySQL. In Compose and Kubernetes the variable is set to the service name, so this fallback only ever applies to local development.

**This machine had MySQL and MongoDB running outside Docker.** Homebrew's `mysql` and `mongodb-community` bind 3306 and 27017 on `127.0.0.1`, which shadows the containers and produces authentication errors that look like a broken compose file. Both are stopped now; restart them with `brew services start mysql` and `launchctl load ~/Library/LaunchAgents/homebrew.mxcl.mongodb-community.plist`. Redis 6379 also collides with the `tikimiki-redis` container from another project.

**Set `JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)`.** The spec says the token is valid for the next hour; EtherBank uses 15 minutes.

### 1.2 Data model

- [x] `models.py` with `User`, `Role`, `UserRole`, modelled on [`docs/materials/Ispit/EtherBank/models.py`](docs/materials/Ispit/EtherBank/models.py).

```
users:      id, forename(256), surname(256), email(256, unique), password(256)
roles:      id, name
user_role:  id, user_id -> users.id, role_id -> roles.id
```

Keep the `secondary = UserRole.__table__` relationship so `user.roles` works. Roles are `director` and `employee`.

**Passwords are hashed**, unlike EtherBank which stores them in plaintext and compares with `User.password == password`. Use `werkzeug.security.generate_password_hash` in `/register` and in `migrate.py` for the seeded director, and `check_password_hash` in `/login`. Werkzeug's default is `scrypt:32768:8:1`, which produces a 162 character string and fits the 256 column with room to spare.

**Do not put a `cascade` on `User.roles`.** A `secondary` relationship already deletes the `user_role` row when the user is deleted, so `POST /delete` needs nothing extra. Adding `cascade = "all, delete"` cascades to the `Role` objects instead: deleting one employee also deletes the `employee` row from `roles`, and the next `/register` then fails on a `None` role. Verified both ways against MySQL before settling on the default.

### 1.3 Validation helpers

- [x] `validation.py` with two helpers you will reuse in all three services:
  - `missing_field(body, names)` returns the first name in `names` that is absent or an empty string, else `None`. Iterating a **list** keeps the order deterministic.
  - `valid_email(value)` with a regex such as `^[^@\s]+@[^@\s]+\.[^@\s]+$`.
  - plus `missing_field_message(name)`, so the graded string with its trailing period is written once rather than at five call sites.

The "empty string counts as missing" rule is easy to miss: `"Field <FIELD_NAME> is missing."` fires both when the key is absent and when the value is a zero-length string.

**Never implement this check with truthiness.** `missing_field` tests `name not in body` and then `isinstance(value, str) and len(value) == 0`, nothing else. Three payloads in this spec are falsy but perfectly valid, and each has its own separate error message that a truthiness check would steal:

| Payload | Endpoint | Correct message |
|---|---|---|
| `"approved": false` | `/decision` | none, it is a valid decision |
| `"buying_price": 0` | `/create_buy_order` | `"Invalid buying price."` |
| `"categories": []` | `/create_buy_order` | `"Categories list is empty."` |

**`/decision` cannot use a single call.** Its order is `uuid` missing → `"Invalid uuid."` → `approved` missing → `"Invalid decision."`, so the uuid is fully validated before `approved` is even looked at. Call `missing_field(body, ["uuid"])`, validate, then `missing_field(body, ["approved"])`. One call with both names would report `approved` missing while an invalid uuid is still unreported.

**Two deliberately literal readings**, worth a sanity check with the professor if the chance comes up:

- An explicit JSON `null` counts as present, since the spec says "nije prisutno ili je vrednost polja string dužine 0" and `null` is neither. No grader is likely to send one.
- `valid_email` checks format only and ignores the 256 character cap, because `"Invalid email."` is the spec's only email error. An over-long address would reach the `String(256)` column and raise instead.

### 1.4 Endpoints

- [x] `POST /register`. Order: missing field (`forename`, `surname`, `email`, `password`) → `"Invalid email."` → `"Invalid password."` (len < 8) → `"Email already exists."`. On success create the user with the **employee** role and return `200` with an empty body.
- [x] `POST /login`. Order: missing field (`email`, `password`) → `"Invalid email."` → `"Invalid credentials."`. Return `{"accessToken": ...}`.
- [x] `POST /delete`. `@jwt_required()`, resolve the user from the JWT identity, `"Unknown user."` if gone, else delete and return `200`.

**Claims.** Identity is the email. Additional claims carry `forename`, `surname`, `email` (same names as registration, no password) plus the role indicator. Follow the course convention and use `"roles": [name for each role]`, matching [`docs/materials/Ispit/EtherBank/decorators.py`](docs/materials/Ispit/EtherBank/decorators.py) so `@role_check("employee")` works unchanged.

**Return shape.** Note `create_access_token` output goes in a field named `accessToken`, not `access_token` as in the examples.

**Read the body with `request.get_json ( silent = True ) or { }`.** The examples index `request.json` directly, which raises `415 Unsupported Media Type` as HTML when the request arrives without a JSON content type, and `400 Bad Request` on malformed JSON. Both replace the graded `{"message": ...}` body with something the grader cannot parse. The `or { }` also covers a literal `null` body, which then falls through to `"Field forename is missing."` as it should.

**Guard the password type before measuring it.** `len ( 12345678 )` raises, and in `/login` `check_password_hash` raises `TypeError` on a non-string. A JSON number in `password` therefore has to be caught: `/register` treats it as `"Invalid password."` and `/login` as `"Invalid credentials."`, which is the closest the spec's fixed message list gets to a type error.

**`/register` depends on the `employee` row already existing.** `Role.query.filter ( Role.name == "employee" ).first ( )` returns `None` on an unseeded database and the append then fails, so the migration Job in 5.2 is what makes registration work at all. Seed roles by hand when running against a fresh local MySQL.

**Port 5000 is not free on macOS.** AirPlay Receiver listens on it and answers every request with an empty `403`, which looks exactly like a broken route in the service. Flask still reports "Running on http://localhost:5000" and loses. Use another port locally (5100 works) or turn AirPlay Receiver off in System Settings > General > AirDrop & Handoff. Containers publish 5000 internally and are unaffected.

### 1.5 Done when

- [x] `curl` register → login → decode the token on jwt.io and confirm the claims
- [x] A register call with `{"forename": "", "email": "bad"}` returns `"Field forename is missing."`, not the email error

---

## Section 2: Employee search

The hardest query logic in the project. Doing it second means the asset document shape is settled before anything writes assets.

### 2.1 Asset document

Fix this shape now and never deviate:

```python
{
  "_id": ObjectId,
  "name": str,
  "categories": [str],
  "buying_price": number,
  "buying_date": datetime,     # native BSON datetime, NOT a string
  "selling_price": number,     # absent until sold
  "selling_date": datetime,    # absent until sold
  "info": { ... }              # arbitrary nesting
}
```

**Store dates as BSON `datetime`, not strings.** Range comparisons on ISO strings happen to work for this format but break the moment a timezone offset differs, and `$gt` on a `datetime` is what the grader will exercise. Convert to ISO 8601 with a `Z` suffix only on the way out.

- [x] Helper `parse_iso(value)`: `datetime.fromisoformat(value.replace("Z", "+00:00"))`
- [x] Helper `serialize(asset)`: `str(_id)` into `id`, datetimes back to ISO 8601, omit `selling_*` when absent

**Serialize with `value.isoformat(timespec="milliseconds") + "Z"`.** It reproduces the spec's `2026-06-08T22:12:00.000Z` exactly. This is only correct because PyMongo hands back **naive** datetimes in UTC by default; passing `tz_aware = True` to `MongoClient` would make `isoformat` emit its own `+00:00` and the result would end in `+00:00Z`. So do not turn that flag on.

**Everything written to Mongo has to be UTC**, because `parse_iso` turns the incoming `Z` into an aware UTC datetime and PyMongo converts it to UTC before comparing. `datetime.now()` returns naive **local** time, which MongoDB then reads as if it were UTC, so on this machine every write would land two hours in the future and searches would disagree with reality by that much. Write `datetime.now(timezone.utc)` in section 3.3 instead.

### 2.2 Query construction

- [x] `POST /search` with `@role_check("employee")`. All fields optional, so build the filter incrementally:

```python
conditions = []
if name:         conditions.append({"name": {"$regex": re.escape(name)}})
if category:     conditions.append({"categories": category})
if buying_date:  conditions.append({"buying_date": {"$gt": parse_iso(buying_date)}})
if selling_date: conditions.append({"selling_date": {"$lt": parse_iso(selling_date)}})
for f in info_filters:
    conditions.append({f"info.{f['field']}": {f"${f['operator']}": f["value"]}})

query = {"$and": conditions} if conditions else {}
```

Three things worth understanding here:

- **`categories: category` matches inside the array.** Mongo compares a scalar against every element, so no `$elemMatch` needed.
- **Use `$and`, not one flat dict.** Two `info_filters` on the same path would collide as duplicate dict keys and the second would silently win.
- **`selling_date: {"$lt": ...}` excludes unsold assets for free.** A document missing the field never matches a range query, which is exactly the "Neprodate imovine ne treba uključiti u rezultat" rule. Do not add extra filtering.
- **`operator` arrives without the `$`.** The spec example is `"operator": "eq"`, so prepend it. The dotted `field` path is relative to `info`, hence the `f"info.{...}"` prefix.

**Read optional fields with `body.get(name) is not None`, not `if name in body`.** A JSON `null` would otherwise reach `re.escape` or `parse_iso` and raise, and `/search` has no error message to return for it: the spec lists only the missing-header `401` here. Treating `null` as "field not given" is the only reading that keeps the endpoint answering `200`.

**`role_check` lives in `decorators.py`**, copied from the course example. A director token gets `("Invalid role", 401)`, a shape the spec never mentions because it only describes the missing-header case.

### 2.3 Done when

- [x] Hand-insert three assets in adminer or `mongosh`, one unsold, and confirm a `selling_date` search omits it
- [x] A nested `info_filters` entry like `{"field": "engine.power", "operator": "gt", "value": 100}` filters correctly

---

## Section 3: Redis order flow

This closes the loop: an employee proposes, the director sees it, the director decides, Mongo changes.

### 3.1 Redis layout

- [x] One hash keyed by uuid. It gives you write, list, and delete in one call each:

```python
redis.hset("orders", order_uuid, json.dumps(order))   # create
redis.hgetall("orders")                               # pending_orders
redis.hdel("orders", order_uuid)                      # decision
```

`hgetall` returns bytes for both keys and values, so `key.decode()` and `json.loads(value)`. Store `order_type` (`"BUY"` / `"SELL"`) inside the JSON so `/pending_orders` can shape each entry.

For pub/sub-style Redis usage in this course see [`docs/materials/Docker/JWT_ban/user.py:37-51`](docs/materials/Docker/JWT_ban/user.py), though a plain hash is the right tool here.

### 3.2 Employee write endpoints

- [x] `POST /create_buy_order`. Order: missing field (`name`, `categories`, `buying_price`, `info`) → `"Categories list is empty."` → `"Invalid buying price."`. Store with a fresh `uuid.uuid4()` and return `200` empty.
- [x] `POST /create_sell_order`. Order: missing field (`id`, `selling_price`) → `"Invalid id."` → `"Invalid selling price."`.

**`"Invalid id."` is two checks in one.** It fires both when the string is not a well-formed `ObjectId` and when no asset with that id exists in Mongo. Wrap `ObjectId(value)` in a `try` and follow it with a `find_one`. Catch `TypeError` next to `InvalidId`: a JSON number in `id` raises the former, and both mean the same thing to the grader.

**Price validation is type-sensitive.** `"Invalid buying price."` covers "not a number" and "<= 0". Guard against `bool`, since `isinstance(True, int)` is `True` in Python. Lives in `validation.py` as `valid_price`, shared by both endpoints.

**A `categories` that is not a list also gets `"Categories list is empty."`** The spec never names that case, and every other reading is worse: a bare string would pass a plain length check and then be stored where `$unwind` and the `categories: category` match both expect an array. Checking `isinstance(value, list)` first keeps the stored shape honest.

### 3.3 Director read and decide

- [x] `GET /pending_orders` with `@role_check("director")`. Emit the common `uuid` and `order_type`, then the BUY-only or SELL-only fields per the spec.
- [x] `POST /decision`. Order: `"Field uuid is missing."` → `"Invalid uuid."` → `"Field approved is missing."` → `"Invalid decision."`.

**`"Invalid uuid."` is also two checks:** malformed UUID (validate with `uuid.UUID(value)`) or no such entry in the Redis hash.

**`"Invalid decision."` means not a real boolean.** `approved` must be JSON `true`/`false`. Reject `"true"` and `1` with `isinstance(value, bool)`.

**`approved` gets no empty-string clause, and that asymmetry is deliberate.** The spec spells `uuid` out as "nije prisutno **ili je vrednost polja string dužine 0**" but writes `approved` as "nije prisutno" alone. So `{"uuid": "<valid>", "approved": ""}` must answer `"Invalid decision."`, not `"Field approved is missing."`. Test `"approved" not in body` directly here rather than reusing `missing_field`, which would steal the empty string.

**Do not use `if not approved` to branch.** `approved` has already been validated as a bool, but writing `if approved is True` documents the intent and survives a later refactor.

On approve:
- BUY → `insert_one` a new asset with `buying_date = datetime.now(timezone.utc)` (the moment of approval, not of proposal)
- SELL → `update_one` with `$set` for `selling_price` and `selling_date = datetime.now(timezone.utc)`

On approve or reject, `hdel` the order either way.

**Both dates are `datetime.now(timezone.utc)`, never a bare `datetime.now()`.** See the note in 2.1: naive local time is two hours off on this machine and MongoDB would store it as if it were UTC. Verified against `mongosh` after a live approval, the stored instant matches UTC wall clock rather than CEST.

### 3.4 Done when

- [x] `scenario.py` runs register → login → create_buy_order → (director) pending_orders → decision approve → search finds the new asset
- [x] A rejected order vanishes from `pending_orders` and creates nothing in Mongo

`scenario.py` reads `AUTHENTICATION_URL`, `EMPLOYEE_URL` and `DIRECTOR_URL` from the environment, defaulting to `localhost:5000/5001/5002` the way `deployment.yaml` will publish them. Locally the ports have to be moved off 5000 because of the AirPlay collision in 1.5, so the run is:

```
AUTHENTICATION_URL=http://localhost:5100 EMPLOYEE_URL=http://localhost:5101 DIRECTOR_URL=http://localhost:5102 python scenario.py
```

It needs the seeded director, so run `python migrate.py` against a fresh database first.

---

## Section 4: Report aggregation

One endpoint, but it is the PyMongo aggregation showcase.

### 4.1 Pipeline

- [x] `GET /report` with `@role_check("director")`:

```python
pipeline = [
    {"$match": {"selling_date": {"$exists": True}, "selling_price": {"$exists": True}}},
    {"$unwind": "$categories"},
    {"$group": {
        "_id": "$categories",
        "spent":  {"$sum": "$buying_price"},
        "earned": {"$sum": "$selling_price"},
    }},
    {"$sort": {"earned": -1, "spent": 1, "_id": 1}},
    {"$project": {"_id": 0, "category": "$_id", "spent": 1, "earned": 1}},
]
```

`$unwind` on `categories` is what implements "ako imovina pripada većem broju kategorija, računa se u statistiku svake": one document becomes N, each contributing its full buying and selling price to a different group. That is the spec's rule, not double counting.

The three-key `$sort` maps directly onto "opadajuće po `earned`, zatim rastuće po `spent` i na kraju rastuće po imenu kategorije". Keep `$sort` before `$project` so it sorts on `_id` while that field still exists.

### 4.2 Open question worth asking the professor

The spec says "U obračun zarade ulazi samo imovine koje su prodate". It is ambiguous whether that restricts the **whole** report or only the `earned` column:

- **Reading A (used above):** unsold assets are excluded entirely, so `spent` only counts assets that were later sold.
- **Reading B:** every asset contributes to `spent`, but only sold ones contribute to `earned`.

Reading A is the more natural parse of "obračun zarade" as the statistic as a whole, and it keeps `spent` and `earned` comparable per category. Reading B is a one-line change (drop the `$match`, wrap the `earned` sum in a `$cond`). Confirm before the defense. `tests/test_report.py::test_an_unsold_asset_contributes_to_neither_column` is the test that pins the choice down, so switching readings means editing that one test and the `$match`.

**The `$match` demands both `selling_price` and `selling_date`.** The spec defines a sold asset as one that has both ("imovina koja ima definisanu cenu prodaje i datum prodaje"), and `/decision` only ever writes the pair together, so a document carrying one without the other is corrupt and stays out of the report.

### 4.3 Done when

- [x] An asset in two categories shows its full price in both rows
- [x] Two categories with equal `earned` come back ordered by ascending `spent`

---

## Section 5: Docker and Kubernetes

The app is feature-complete at this point (minus voting). Now make it deployable.

### 5.1 Dockerfiles

- [x] One per service, copying only what that service imports. Template: [`docs/materials/Ispit/EtherBank/authentication.dockerfile`](docs/materials/Ispit/EtherBank/authentication.dockerfile).
- [x] `deployment.yaml` for Compose, everything containerized, modelled on [`docs/materials/Ispit/EtherBank/deployment.yaml`](docs/materials/Ispit/EtherBank/deployment.yaml). Get this green before touching k8s: it is the same env-var wiring with far faster feedback.

`authentication` copies `models.py` and `validation.py`; `employee` and `director` copy `decorators.py` and `validation.py` but no models, since neither speaks SQL. All four install the one `requirements.txt`. `mysqlclient` compiles on plain `python:3` with no extra apt packages, so the course's bare `FROM python:3` needs nothing added.

**Compose starts things in the right order with two conditions rather than a wait script.** `database` gets a `mysqladmin ping` healthcheck, `migration` waits for `service_healthy`, and `authentication` waits for the migration's `service_completed_successfully`. The employee and director services only need `mongo` and `redis`, both of which their clients connect to lazily.

**The published ports are `${AUTHENTICATION_PORT:-5000}` and friends.** The defaults are the 5000/5001/5002 that `scenario.py` expects, but on this machine Docker cannot even bind 5000 (`address already in use`, the AirPlay collision from 1.5 again), and unlike Flask it fails loudly. So locally: `AUTHENTICATION_PORT=5100 docker compose -f deployment.yaml up -d`.

### 5.2 Migration image

The course runs schema creation as a **`kind: Job`**, never an initContainer, and never mounts `init.sql` in k8s. See [`docs/materials/k8s/examples/migration.yaml`](docs/materials/k8s/examples/migration.yaml) and [`docs/materials/k8s/examples/employees/migrate.py`](docs/materials/k8s/examples/employees/migrate.py).

- [x] `migrate.py`: a minimal Flask app that runs `database.create_all()` inside `app_context()`, then **seeds the roles and the initial director**:

```json
{"forename": "Scrooge", "surname": "McDuck",
 "email": "onlymoney@gmail.com", "password": "evenmoremoney"}
```

Make the seed idempotent (check for the email before inserting). The Job can be retried by Kubernetes and must not fail or duplicate on a second run. Written early, out of section order, because `scenario.py` in 3.4 cannot log a director in without it. Verified by running it twice against the same database.

- [x] Separate `migration.dockerfile` copying `configuration.py`, `models.py`, `migrate.py`.

### 5.3 The graded k8s file

The spec's explicit requirements, mapped to the course's house style:

| Requirement | How |
|---|---|
| All config in `ConfigMap` | `envFrom: [configMapRef: {name: ...}]`, per [`docs/materials/k8s/presentation/k8s.md:424`](docs/materials/k8s/presentation/k8s.md) |
| All passwords in `Secret` | `type: Opaque` + `stringData:`, consumed via `secretKeyRef`, per [`docs/materials/k8s/examples/mysql-storage.yaml`](docs/materials/k8s/examples/mysql-storage.yaml) |
| Data survives restarts | `PersistentVolume` + `PersistentVolumeClaim` for **both** MySQL and Mongo |
| Employee service in 3 replicas | `replicas: 3` on that Deployment only |
| Auto-init of the relational DB | the migration `Job` from 5.2 |

- [ ] Write `k8s.yaml` as one multi-document file so the defense is a single `kubectl apply -f k8s.yaml`.

**Heads up on the examples.** The k8s examples in this repo mostly do *not* use ConfigMap (they inline `value: "root"`) and run MySQL as a bare `kind: Pod`. The spec explicitly requires ConfigMap and Secret, so follow the spec over the examples here. Borrow the persistence block from `mysql-storage.yaml`, which is the one example that does it properly: `storageClassName: ""` on both PV and PVC plus an explicit `volumeName:` for static binding.

- [ ] Services: `ClusterIP` for the databases, `NodePort` for the three web services so you can reach them during the demo.
- [ ] `DATABASE_URL` is the **Service name** (the examples pass `"mysql-service"`), resolved by cluster DNS.

**On readiness:** the course examples have no wait-for-DB logic at all and lean on `backoffLimit: 4` with `restartPolicy: Never` so the Job just retries until MySQL accepts connections. That is acceptable, but a readiness probe (`mysqladmin ping`, see [`docs/materials/k8s/examples/mysql-probes.yaml`](docs/materials/k8s/examples/mysql-probes.yaml)) makes the live demo far less nerve-wracking.

### 5.4 Done when

- [ ] `kubectl apply -f k8s.yaml` on a clean cluster brings everything up and `scenario.py` passes against the NodePorts
- [ ] `kubectl delete pod <mysql-pod>` and the data is still there afterwards
- [ ] `kubectl get pods` shows 3 employee pods

---

## Section 6: Voting via smart contract

This **replaces** the working `/decision` from section 3, so branch or copy it before you start.

### 6.1 The contract

- [ ] `voting.sol`, in the style of [`docs/materials/Ispit/CourierService/delivery.sol`](docs/materials/Ispit/CourierService/delivery.sol) (constructor takes the participants, `require` guards with exact messages):

```solidity
pragma solidity ^0.8.18;

contract Voting {
    mapping ( address => bool ) allowed;
    mapping ( address => bool ) voted;
    uint approve_count;
    uint reject_count;
    uint majority;
    bool ended;
    bool approved;

    constructor ( address[] memory _voters ) {
        require ( _voters.length % 2 == 1, "Even number of voters." );
        for ( uint i = 0; i < _voters.length; i++ ) allowed[_voters[i]] = true;
        majority = _voters.length / 2 + 1;
    }

    modifier can_vote {
        require ( !ended, "Voting ended." );
        require ( allowed[msg.sender], "Invalid address." );
        require ( !voted[msg.sender], "Already voted." );
        _;
    }

    function vote_approve ( ) external can_vote { ... }
    function vote_reject  ( ) external can_vote { ... }
    function status ( ) external view returns ( bool, bool ) { return ( ended, approved ); }
}
```

**Check `ended` before `allowed`.** The spec says *every* attempt after conclusion is rejected with `"Voting ended."`, so that guard has to come first or a late non-voter would get `"Invalid address."` instead.

- [ ] Compile with `py-solc-x` or `solcjs` to `output/Voting.abi` and `output/Voting.bin`, and commit them. Every course example ships the compiled artifacts rather than compiling at runtime.

### 6.2 Rewrite `/decision`

- [ ] New body is `uuid` + `voters`. Order: `"Field uuid is missing."` → `"Invalid uuid."` → `"Field voters is missing."` (absent **or empty list**) → `"Invalid voter address."` → `"Even number of voters."`
- [ ] Validate addresses with `web3.is_address(...)`.
- [ ] Deploy the contract, paying from a ganache account. The pattern is [`docs/materials/Ispit/EtherBank/administrator.py:37-53`](docs/materials/Ispit/EtherBank/administrator.py): read the `.abi` and `.bin`, `web3.eth.contract(bytecode=..., abi=...)`, `contract.constructor(voters).build_transaction({...})`, sign, send, take `receipt["contractAddress"]`.
- [ ] Copy [`docs/materials/Ispit/EtherBank/utilities.py`](docs/materials/Ispit/EtherBank/utilities.py) for `get_web3` and `send_transaction`.

### 6.3 Two design decisions

**Which account pays.** The spec says to pay from one of the accounts ganache creates at startup. Simplest is `web3.eth.accounts[0]` with ganache's unlocked default, which avoids EtherBank's encrypted-keystore dance in `get_administrator_account`.

**What shape the returned transactions take.** The spec returns a single `approve_transaction` / `reject_transaction` pair, but the sender is not known at build time (any of the voters may cast it). So do not bake in `from` and `nonce` the way [`docs/materials/Ispit/CourierService/customer.py:34-40`](docs/materials/Ispit/CourierService/customer.py) does for a known customer. Return `to`, `data`, `gas`, `gasPrice` and let the voter fill in `from` and `nonce` before signing.

### 6.4 Detecting that voting ended

This is the genuinely hard part: the contract concludes at a moment your Flask service is not involved in, yet the service must then write to Mongo and clear Redis.

- [ ] Keep a registry of live contracts, for example a Redis hash `contracts` mapping `uuid` to contract address, written when `/decision` deploys.
- [ ] Run a background thread in the director service that polls `status()` for each live contract every few seconds. On conclusion: if approved, apply the same Mongo write as section 3.3 (BUY inserts, SELL updates, dates set to the moment of approval); either way remove the order from Redis and the contract from the registry.

Polling is the pragmatic choice on ganache over HTTP. The alternative is emitting a Solidity event and using `contract.events.<Name>.create_filter(...)`, which is cleaner but still needs a polling loop with `HTTPProvider`. Either way this thread starts alongside the app, the same way [`docs/materials/Docker/JWT_ban/user.py:88`](docs/materials/Docker/JWT_ban/user.py) starts its Redis listener.

**With 3 replicas of the employee service this is fine**, since the poller lives in the director service. Keep the director at 1 replica or several pollers will race to apply the same approval.

### 6.5 Done when

- [ ] A non-voter address gets `"Invalid address."`, a double vote is rejected, and a vote after conclusion gets `"Voting ended."`
- [ ] 3 voters, 2 approvals, and the asset appears in Mongo without any further director call
- [ ] Even-length `voters` is rejected by the endpoint before deployment, and by the constructor as a backstop

---

## Defense checklist

- [ ] `kubectl apply -f k8s.yaml` from scratch on a clean cluster
- [ ] Log in as the seeded `onlymoney@gmail.com` director
- [ ] Register an employee, propose a buy, approve it by vote, show it in `/search` and `/report`
- [ ] Kill a database pod, show the data survived
- [ ] Show 3 employee replicas serving traffic
