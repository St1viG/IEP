# Uputstvo za pokretanje

Korak po korak, od praznog racunara do sistema koji radi i testova koji prolaze.
Komande su za Windows (`cmd`); na Mac-u i u Git Bash-u je ista stvar sa `sh ime.sh`
umesto `ime.cmd`.

Kraca verzija za podsecanje je [`KOMANDE.md`](KOMANDE.md), detaljna po temama
[`SETUP.md`](SETUP.md).

---

## Korak 0 — sta mora da postoji

Potreban je **samo Docker Desktop**. Python na racunaru nije potreban: i testovi i
provera ruta se vrte u kontejneru.

```cmd
docker --version
docker compose version
```

Ako `docker --version` radi a `docker info` puca, Docker Desktop nije pokrenut —
pokreni ga i sacekaj da ikona prestane da se animira. Na fakultetskim racunarima
Docker jeste instaliran, ali korisnik ponekad nema privilegije za njega — trazi to
od dezurnog cim sednes, pre nego sto pocnes bilo sta drugo.

Za Kubernetes deo dodatno:

```cmd
kubectl version --client
```

---

## Korak 1 — uzmi projekat

```cmd
git clone https://github.com/St1viG/IEP.git
cd IEP
```

Sve komande ispod se pokrecu **iz korena projekta**, tj. iz foldera `IEP`.

---

## Korak 2 — slike

Cetiri projektne slike se grade lokalno, a biblioteke mogu sa PyPI-ja ili iz
`wheels/` bez mreze — vidi Korak 2b.

Sedam javnih slika mora odnekud da dodje:

```
python:3   mysql   mongo:7   redis   trufflesuite/ganache-cli   busybox:1.36   adminer
```

- Ako Docker Hub radi, ne radi nista — povuci ce se same u sledecem koraku.
- Ako ih neko deli kao `.tar` fajlove, ucitaj svaki:

```cmd
docker load -i python-3.tar
docker load -i mysql-latest.tar
```

Provera sta vec imas:

```cmd
docker images
```

---

## Korak 2b — biblioteke: sa mreze ili iz `wheels/`

Postoje dva nacina, i oba rade. Bira se u trenutku build-a, bez diranja koda.

**Sa PyPI-ja (podrazumevano, treba mreza).** Tako je i u arhivi koja se predaje,
gde `wheels/` ne postoji jer ne bi stao u ogranicenje velicine:

```cmd
pokreni.cmd
```

odnosno rucno:

```cmd
docker compose -f deploy/deployment.yaml build
```

**Iz `wheels/`, bez ikakve mreze.** Prvo napuni folder jednom, dok mreza jos
postoji, pa gradi bez nje:

```cmd
sh spakuj-wheels.sh
docker compose -f deploy/deployment.yaml build --build-arg PIP_ARGS="--no-index --find-links /wheels"
```

`spakuj-wheels.sh` povuce sve sto `requirements.txt` trazi, za obe arhitekture, i
odmah proveri da instalacija prolazi sa iskljucenom mrezom. Zauzme oko 41 MB.

Ako `wheels/` postoji u kloniranom repozitorijumu, drugi nacin radi odmah — ne
treba ni skripta.

---

## Korak 3 — pokreni sistem

```cmd
pokreni.cmd
```

Skripta obrise staro stanje, izgradi cetiri slike, podigne sve i sacekati da
servisi pocnu da odgovaraju. Prvi put traje nekoliko minuta, svaki sledeci put
nekoliko sekundi.

Na kraju ispisuje:

```
Sistem radi:
  authentication  http://localhost:5000
  employee        http://localhost:5001
  director        http://localhost:5002
  ganache         http://localhost:8545
  adminer         http://localhost:8080
```

Provera da su svi kontejneri gore:

```cmd
docker ps
```

Ocekuje se osam: `authentication`, `employee`, `director`, `database`, `mongo`,
`redis`, `ganache`, `adminer`. Kontejner `migration` je zavrsio posao i stoji na
`Exited (0)` — tako i treba.

Direktor je vec u bazi: `onlymoney@gmail.com` / `evenmoremoney`.

---

## Korak 4 — proveri da radi

```cmd
deploy\proveri.cmd director /report
```

```
GET http://host.docker.internal:5002/report -> 200
{
  "statistics": []
}
```

Skripta sama uradi login i doda token, tako da ne treba ni `curl` ni Postman.
Jos par primera:

```cmd
deploy\proveri.cmd director /pending_orders
deploy\proveri.cmd employee /search name=Ferrari
deploy\proveri.cmd employee /create_sell_order id=nesto selling_price=200
```

Telo zahteva se pise kao `key=value`. **Ne pisi JSON sa `\"`** — `cmd` to ne
razume i stigne izlomljeno. Vrednost koja lici na JSON se salje kao JSON, pa je
`selling_price=200` broj, a `approved=true` logicka vrednost.

---

## Korak 5 — testovi

Testovima trebaju baze objavljene na host portovima, sto radi `development.yaml`,
a ne `deployment.yaml`. Zato prvo spusti jedno pa digni drugo:

```cmd
docker compose -f deploy/deployment.yaml down
docker compose -f deploy/development.yaml up -d
testovi.cmd
```

Ocekivano:

```
174 passed in 26.00s
```

**Gledaj da nema preskocenih.** Ako baze nisu podignute, testovi se ne rusе nego
se preskacu i izlaz je `33 passed, 141 skipped` — sto lici na uspeh a nije.
Prolaz koji nesto dokazuje kaze **174 passed** i ne pominje skip.

Moze i deo po deo:

```cmd
testovi.cmd -m "not integration"    :: 33 koji ne traze nijedan servis
testovi.cmd -k report -v            :: samo izvestaj, detaljno
testovi.cmd -x                      :: stani na prvoj gresci
```

Kad zavrsis sa testovima, vrati pun sistem:

```cmd
docker compose -f deploy/development.yaml down
pokreni.cmd
```

---

## Korak 6 — Kubernetes

Prvo se ukljucuje u **Docker Desktop → Settings → Kubernetes → Enable Kubernetes**,
pa se saceka da indikator pozeleni. Prvo ukljucivanje traje par minuta.

```cmd
docker compose -f deploy/deployment.yaml down
pokreni-k8s.cmd
```

Skripta izgradi slike, ubaci ih u klaster, primeni manifest, saceka svaki
deployment i migracioni Job, i otvori port-forward-ove.

```cmd
kubectl get pods
```

```
authentication-…   1/1  Running
director-…         1/1  Running
employee-…         1/1  Running     x3
ganache-…          1/1  Running
migration-job-…    0/1  Completed
mongo-…            1/1  Running
mysql-…            1/1  Running
redis-…            1/1  Running
```

Servisi su na istim portovima kao i ranije (5000 / 5001 / 5002), preko
port-forward-a, pa `deploy\proveri.cmd` radi nepromenjen.

**`load-images` nije opcion.** `k8s.yaml` koristi `imagePullPolicy: Never` za
cetiri nase slike, a klaster ima svoj image store koji ne vidi slike Docker
demona — `docker build` sam po sebi nije dovoljan. To radi `pokreni-k8s.cmd`,
odnosno `deploy\load-images.cmd` ako ides rucno.

Rusenje:

```cmd
kubectl delete -f deploy/k8s.yaml
```

---

## Korak 7 — zvanicni grader (opciono, za vezbu)

Grader nije u repozitorijumu; treba prekopirati `docs\ProjekatExample\` pored
projekta.

```cmd
resetuj.cmd
oceni.cmd
```

```
TOTAL: 179.00/179.00 (100.00%)
```

**`resetuj.cmd` pre svakog prolaza.** Grader je stateful i racuna na praznu bazu,
pa drugi prolaz nad podacima iz prvog daje oko 79% — to nije greska u kodu.

Za Kubernetes varijantu:

```cmd
resetuj.cmd k8s
pokreni-k8s.cmd
oceni.cmd k8s
```

---

## Korak 8 — modifikacija uzivo

Ovo se radi na odbrani i **uslov je za bodove**. Detaljno, sa gotovim obrascima,
u [`MODIFIKACIJE.md`](MODIFIKACIJE.md).

Podigni sistem tako da se izvorni kod montira u kontejnere:

```cmd
docker compose -f deploy/deployment.yaml -f deploy/live.yaml up -d
```

Onda je petlja:

```cmd
copy src\director.py src\director.py.bak

:: izmeni src\director.py

docker compose -f deploy/deployment.yaml -f deploy/live.yaml restart director
deploy\proveri.cmd director /nova_ruta
python deploy\proveri-kod.py
```

Restart traje oko cetiri sekunde — bez build-a, bez `pip`-a, bez mreze.

Na kraju obavezno:

```cmd
resetuj.cmd
oceni.cmd
```

Mora ostati **179/179**. Postojece ponasanje mnozi bodove; nova ruta vredi mnogo
manje od devet koje vec rade.

---

## Ako nesto pukne

| Vidis | Sta je | Sta da uradis |
|---|---|---|
| `docker info` puca | Docker Desktop ne radi | pokreni ga; na fakultetu trazi privilegije |
| `ErrImageNeverPull` | slika nije u image store-u klastera | `deploy\load-images.cmd` |
| `ImagePullBackOff` | javna slika nije lokalno | `docker load -i <fajl>` ili `docker pull` |
| `/search` visi ~30 s, `/report` 500, `/pending_orders` radi | Mongo je nedostupan | slika mora biti `mongo:7`; verzija 8 nece da startuje na kernelu 6.19+ |
| mongo pod `Error`, exit 62 | volumen je pisala novija verzija Mongo-a | `resetuj.cmd k8s` |
| migration `Completed` a niko ne moze da se loguje | Job je vec zavrsio i nece ponovo | `kubectl delete job migration-job` pa `kubectl apply -f deploy/k8s.yaml` |
| testovi preskacu umesto da rade | baze nisu podignute | `docker compose -f deploy/development.yaml up -d` |
| grader drugi put daje ~79% | grader trazi praznu bazu | `resetuj.cmd` pa opet |
| grader: `unrecognized arguments` | zaostao `grade_report.json` | obrisi ga |
| CoreDNS `CrashLoopBackOff`, exit 139 | klaster je pravljen dok je disk bio pun | oslobodi disk, pa `docker desktop kubernetes reset-cluster` |
| `read-only file system` bilo gde u Dockeru | disk je pun | oslobodi mesto na hostu, restartuj Docker, `docker builder prune -af` |
| `address already in use` na 5000 | samo na Mac-u, AirPlay | `AUTHENTICATION_PORT=5100 EMPLOYEE_PORT=5101 DIRECTOR_PORT=5102 sh pokreni.sh` |

Prati koliko ima slobodnog prostora na disku. Kad se host napuni, Docker-ov VM
predje u read-only i greske koje posle toga ispisuje ne pominju disk nijednom.
