# Odbrana — sta pokazati i sta reci

Srpska verzija [`DEFENSE.md`](DEFENSE.md). Redosled pokretanja je u
[`UPUTSTVO.md`](UPUTSTVO.md), komande na jednoj strani u [`KOMANDE.md`](KOMANDE.md),
modifikacija u [`MODIFIKACIJE.md`](MODIFIKACIJE.md).

## Kako se boduje

30 poena kod + 15 Kubernetes + 15 blockchain, maksimum 60, i sve to **pomnozeno
procentom testova koji prodju posle modifikacije**. Modifikacija je uslov — bez
nje nema poena uopste.

Prakticno znaci: prvo podigni sistem, pa uradi modifikaciju, i iznad svega **ne
polomi devet ruta koje vec rade**. Nova ruta vredi mnogo manje od njih.

Tri pravila koja asistenti proveravaju, a projekat ih vec ispunjava:

- `/report` mora kroz MongoDB aggregation framework — ide:
  `$unwind → $group → $sort → $project`.
- Sirov SQL nije dozvoljen, mora ORM — `authentication.py` nigde ne sastavlja SQL
  string.
- Filtrira se upitom, ne Python petljom. Jedini legitiman izuzetak je Redis, koji
  nema upitni jezik — to reci naglas pre nego sto te pitaju.

Provereno: **179/179 (100%)** na zvanicnom grader-u, na svim nivoima ukljucujuci
blockchain, i to tri puta zaredom kroz Kubernetes, sa svim podovima na nula
restartova.

## Sta pokazati, tim redom

Svaka tacka odgovara jednom zahtevu iz postavke.

**1. Ceo sistem se dize jednom komandom.**
`pokreni-k8s.cmd`, pa `kubectl get pods`. Jedan `kubectl apply -f deploy/k8s.yaml`
podigne sve: `ConfigMap`, `Secret`, dva `PersistentVolume`-a, migracioni `Job` i
cetiri servisa.

**2. Tri replike.**
`kubectl get pods -l app=employee` → tri poda. Servis zaposlenih je jedini koji
se skalira, jer je jedini koji opsluzuje sve korisnike.

**3. Trajnost podataka.**
`kubectl delete pod -l app=mysql`, sacekaj novi pod, pa se **ponovo uloguj bez
restartovanja ijednog servisa**. Podaci su preziveli pod, a servis je prezive
promenu adrese — to drugo je `pool_pre_ping`. Isto i za `-l app=mongo`: `/search`
i dalje vraca imovinu.

**4. Ceo tok, od predloga do knjizenja.**
Uloguj direktora `onlymoney@gmail.com` / `evenmoremoney`, registruj zaposlenog,
posalji predlog kupovine, otvori glasanje sa `/decision`, posalji dva od tri
glasa sa ganache naloga, i pokazi da se imovina pojavila u `/search` i `/report`
**bez ijednog daljeg poziva direktoru**. To je cela poenta sekcije sa glasanjem.

**5. Odbijen zahtev ne ostavlja trag.**
Predlozi nesto, glasaj dva puta protiv, pokazi da je nestalo iz `/pending_orders`
i da ga nema u `/search`.

**6. Redosled validacija.**
`{"forename": "", "email": "bad"}` na `/register` vraca `"Field forename is
missing."`, a ne gresku o imejlu. Postavka trazi bas taj redosled.

Ako nesto krene naopako, `python scenario.py` prolazi kroz sve ovo sam i ispisuje
`ok` po koraku.

## Pitanja i odgovori

**Zasto neprodata imovina i dalje ulazi u `spent`?**
Postavka definise `spent` bez ijednog uslova — "ukupan iznos potrosen za kupovinu
imovine koja pripada datoj kategoriji". Recenica koja ogranicava pominje samo
"obracun zarade", dakle `earned`. Znaci imovina koju fond jos drzi donosi svoju
kupovnu cenu u `spent` i nista u `earned`. Zbog toga sortiranje uopste i ima
`spent` kao drugi kljuc: sa neprodatim kategorijama u izvestaju, mnogi redovi se
izjednace na `earned: 0`. Zvanicni grader ocekuje bas to.

**Zasto vracene transakcije nemaju `from` i `nonce`?**
Zato sto se u trenutku deploy-a ne zna ko salje. Bilo koji od dozvoljenih glasaca
moze da posalje bilo koji od dva glasa, a `nonce` je vezan za nalog. Zato
`/decision` vraca `to`, `data`, `gas`, `gasPrice` i `chainId`, a glasac dopuni
ostalo pre potpisivanja. Referentno resenje sa kursa ubacuje `from` i `nonce`
zato sto tamo postoji tacno jedan poznat posiljalac.

**Kako odobren zahtev stigne u MongoDB ako niko ne pozove servis?**
Zaposleni glasaju u trenutku u kojem direktorski servis ne ucestvuje. `/decision`
upise `uuid → adresa ugovora` u Redis hash, a nit u pozadini svake sekunde cita
`status()` svakog zivog ugovora. Kad glasanje zavrsi, ugovor se "preuzme"
atomskim `HDEL`-om — `HDEL` vraca broj obrisanih polja, pa tacno jedan pozivalac
dobije jedinicu — i tek onda se pise imovina i uklanja zahtev. Zbog toga je
bezbedno da i zahtev i nit rade isto: `/pending_orders` i `/report` "poravnaju"
stanje pre nego sto odgovore, pa nikad ne vracaju zastarelo. Isti oblik koristi i
materijal sa kursa, `docs/materials/Docker/JWT_ban/user.py`, gde se Redis
slusalac startuje kao `Thread` pre `application.run`.

**Zasto je direktor u jednoj replici?**
Da postoji jedna nit koja poravnava. Preuzimanje je atomsko, pa bi i vise replika
bilo ispravno, ali nema sta da se dobije — direktor opsluzuje jednog coveka.
Servis zaposlenih, koji opsluzuje sve, je onaj koji postavka trazi da se skalira,
i on je na tri.

**Zasto Redis nema PersistentVolume?**
Postavka ga zove "Redis servis koji se koristi za cuvanje privremenih
informacija". Zahtevi tamo zive samo izmedju predloga i glasanja. Dve baze koje
drze trajno stanje, MySQL i MongoDB, imaju i `PersistentVolume` i
`PersistentVolumeClaim` sa `persistentVolumeReclaimPolicy: Retain`.

**Zasto `--evm-version istanbul` pri prevodjenju ugovora?**
Postavka propisuje sliku `trufflesuite/ganache-cli`, a to je ganache 6, stariji od
`PUSH0` instrukcije koju danasnji `solc` podrazumevano emituje. Deploy takvog
bajtkoda pukne sa golim "invalid opcode" koji ne pominje nijednu verziju.

**Nije li `$unwind` duplo brojanje?**
Nije, to je pravilo iz same postavke: "Ukoliko jedna imovina pripada vecem broju
kategorija, ona se racuna u statistiku svake od tih kategorija." Jedan dokument
postane N, svaki sa punom cenom u drugoj grupi.

**Zasto migracioni Job ima initContainer?**
Izmereno, ne pretpostavljeno. Sa samim `backoffLimit: 4`, kako radi primer sa
kursa, Job je pao tri puta i uspeo tek iz cetvrtog pokusaja, 86 sekundi kasnije,
jer MySQL-u treba oko minut da inicijalizuje prazan direktorijum. Jedan sporiji
disk i pocetni direktor nikad ne bi nastao. Busybox initContainer ceka na
`nc -z mysql-service 3306` i Job posle toga zavrsi za 18 sekundi.

**Zasto kod nije pisan u stilu sa vezbi?**
Postavka propisuje biblioteke, poruke o greskama, imena polja u odgovorima i
artefakte za deploy. O formatiranju ne kaze nista, pa je kod po PEP 8, sto
proveravaju `ruff` i `pre-commit`. Jedini fajl ostavljen tacno kako je na kursu
napisan je `decorators.py`, jer je `role_check` deo API-ja sa vezbi.

**Zasto token za pogresnu ulogu vraca `Missing Authorization Header`?**
Postavka opisuje samo slucaj kad zaglavlje nedostaje. Token koji ne ovlascuje za
tu rutu ne vredi vise od nikakvog tokena, pa dobija isti odgovor — a to je i ono
sto zvanicni grader ocekuje i sto radi referentno resenje.

## Rezervne varijante

- **Kubernetes nece da se digne.** `pokreni.cmd` daje isti sistem na
  5000/5001/5002 kroz Compose, i `scenario.py` radi nepromenjen.
- **Build pukne.** Sve biblioteke su u `wheels/` i `pip` ne izlazi na mrezu; ako
  ipak ne prodje, slike od ranije su vec u lokalnom Docker store-u — preskoci
  build i idi na `load-images`.
- **Port 5000 zauzet** (samo na Mac-u, AirPlay):
  `AUTHENTICATION_PORT=5100 EMPLOYEE_PORT=5101 DIRECTOR_PORT=5102 sh pokreni.sh`.
