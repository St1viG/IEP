# Komande — jedna strana

Sve iz korena projekta. Na Windowsu `.cmd`, na Mac-u i u Git Bash-u `sh …`.

## Podizanje

```
ucitaj-slike.cmd                  ucitaj slike iz images\ (masina bez Docker Hub-a)
pokreni.cmd                       build + start, Compose
pokreni-k8s.cmd                   isto na Kubernetesu, sa port-forward-ovima
oceni.cmd                         zvanicni grader        -> grade_report.json
oceni.cmd k8s                     grader kroz k8s        -> grade_report_k8s.json
testovi.cmd                       174 testa u kontejneru
```

Servisi: **5000** authentication, **5001** employee, **5002** director,
**8545** ganache, **8080** adminer.
Direktor: `onlymoney@gmail.com` / `evenmoremoney`.

## Modifikacija uzivo — bez build-a, bez mreze

```
docker compose -f deploy/deployment.yaml -f deploy/live.yaml up -d
```

Izvorni fajlovi su montirani preko onih u slici, pa posle izmene treba samo:

```
docker compose -f deploy/deployment.yaml -f deploy/live.yaml restart director
deploy\proveri.cmd director /nova_ruta
python deploy\proveri-kod.py                  duplikati ruta i greske u pipeline-ima
oceni.cmd                                     mora ostati 100%
```

Restart traje oko cetiri sekunde. Bez `live.yaml` je `up -d --build director`,
sto na masini bez mreze i bez build kesa trazi PyPI.

Rezervna kopija pre izmene: `copy src\director.py src\director.py.bak`

## Provera ruta

```
deploy\proveri.cmd director /report
deploy\proveri.cmd director /pending_orders
deploy\proveri.cmd employee /search name=Ferrari
deploy\proveri.cmd employee /create_sell_order id=... selling_price=200
```

Telo se pise kao `key=value` — `cmd` ne razume `\"` u navodnicima.
Vrednost koja lici na JSON se salje kao JSON, pa je `selling_price=200` broj.

## Stanje i greske

```
docker ps                                     svi kontejneri Up
docker compose -f deploy/deployment.yaml logs --tail 50 director
docker logs investment-fund-director-1 --tail 50

kubectl get pods                              svi Running, RESTARTS 0
kubectl logs deployment/director --tail 50
kubectl describe pod <ime>
kubectl get svc
```

## Rusenje

```
docker compose -f deploy/deployment.yaml down       zadrzi podatke
docker compose -f deploy/deployment.yaml down -v    obrisi i podatke
kubectl delete -f deploy/k8s.yaml
```

## Ako nesto pukne

| Vidis | Uradi |
|---|---|
| `ErrImageNeverPull` | `deploy\load-images.cmd` |
| `ImagePullBackOff` | slika nije lokalno — `ucitaj-slike.cmd` |
| `/search` visi ~30 s, `/report` 500, `/pending_orders` radi | Mongo je nedostupan; slika mora biti `mongo:7`, 8 ne startuje na kernelu 6.19+ |
| migration `Completed` a niko ne moze da se loguje | `kubectl delete job migration-job` pa `kubectl apply -f deploy/k8s.yaml` |
| CoreDNS `CrashLoopBackOff`, exit 139 | oslobodi disk, pa `docker desktop kubernetes reset-cluster` |
| `read-only file system` bilo gde u Dockeru | disk je pun; oslobodi mesto, restart Dockera, `docker builder prune -af` |
| testovi preskacu umesto da rade | `docker compose -f deploy/development.yaml up -d` |
| grader: `unrecognized arguments` | obrisi zaostali `grade_report.json` |
| port 5000 zauzet (samo Mac) | `AUTHENTICATION_PORT=5100 EMPLOYEE_PORT=5101 DIRECTOR_PORT=5102 sh pokreni.sh` |

## Sta se boduje

30 kod + 15 Kubernetes + 15 blockchain, maksimum 60, **pomnozeno procentom
testova koji prodju posle modifikacije**. Bez modifikacije nema poena.

- `/report` mora kroz Mongo aggregation framework — ide.
- Sirov SQL nije dozvoljen, samo ORM — nema nijednog SQL stringa.
- Filtriraj upitom, ne Python petljom. Izuzetak je Redis, koji nema upitni
  jezik — reci to naglas.

Detaljno: [`MODIFIKACIJE.md`](MODIFIKACIJE.md), [`SETUP.md`](SETUP.md),
[`DEFENSE.md`](DEFENSE.md).
