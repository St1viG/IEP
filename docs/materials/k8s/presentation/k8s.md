---
marp: true
theme: default
size: 16:9
paginate: true
title: Kubernetes
---

<!-- _class: lead -->

# Kubernetes

---

## Kubernetes

- Docker image ostaje osnovna jedinica za pakovanje aplikacije
- Kubernetes, često `k8s`, upravlja pokretanjem tih image-a u klasteru
- U odnosu na ručno pokretanje kontejnera, Kubernetes dodaje:
  - stabilno imenovanje i povezivanje servisa
  - automatsko vraćanje `Pod`-ova nakon pada
  - skaliranje i rolling update
  - konfiguraciju, tajne i trajno skladište

---

## Deklarativni pristup

- Umesto ručnog pokretanja kontejnera, opisuje se željeno stanje
- Kubernetes pokušava da stvarno stanje dovede u željeno stanje
- Primeri željenog stanja:
  - aplikacija treba da ima 3 instance
  - servis treba da bude dostupan na portu 80
  - baza treba da koristi trajno skladište
  - nova verzija aplikacije treba postepeno da zameni staru

---

## Arhitektura ukratko

<style scoped>
pre { font-size: 0.7em; }
</style>

```text
Kubernetes cluster

Control plane
  - API server
  - Scheduler
  - Controller manager
  - etcd

Worker nodes
  - kubelet
  - container runtime
  - kube-proxy
  - pods
```

- `Control plane` komponente čuvaju stanje klastera i donose odluke, ove komponente se mogu izvršavati na "menadžer" serverima, ali ovo nije neophodno
- `Worker node` izvršava aplikacione `Pod`-ove
- Korisnik najčešće radi preko Kubernetes API-ja pomoću alata `kubectl`

---

## `kubectl`

- `kubectl` je komandni alat za rad sa Kubernetes klasterom
- Koristi Kubernetes API
- Omogućava kreiranje, pregled, izmenu i brisanje resursa

```bash
kubectl version
kubectl cluster-info
kubectl get nodes
kubectl get pods
```

---

## Kubernetes resursi

- Kubernetes resursi se najčešće opisuju pomoću `YAML` fajlova
- Svaki resurs obično sadrži:
  - `apiVersion`
  - `kind`
  - `metadata`
  - `spec`
- `metadata.name` definiše ime resursa
- `spec` definiše željeno stanje

---

## Primer resursa

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
    - name: nginx
      image: nginx:latest
      ports:
        - containerPort: 80
```

```bash
kubectl apply -f pod.yaml
kubectl get pods
```

---

## `Pod`

- `Pod` je najmanja izvršna jedinica u Kubernetes-u
- Jedan `Pod` može sadržati jedan ili više kontejnera
- Kontejneri unutar istog `Pod`-a dele: mrežni prostor, IP adresu, portove, diskove
- U praksi, jedan `Pod` najčešće sadrži jedan glavni kontejner

---

## Pod nije isto što i kontejner

- Kontejner pokreće proces aplikacije
- `Pod` je Kubernetes omotač oko jednog ili više povezanih kontejnera
- Kubernetes raspoređuje i prati `Pod`-ove, a ne pojedinačne kontejnere
- Ako `Pod` nestane, njegov IP se može promeniti => zbog toga se za stabilan pristup koristi Service

---

## Životni ciklus `Pod`-a

- Pod može biti u različitim stanjima: `Pending`, `Running`, `Succeeded`, `Failed`, `Unknown`
- Korisne komande:

```bash
kubectl get pods
kubectl describe pod nginx
kubectl logs nginx
kubectl exec -it nginx -- /bin/sh
```

---

## Problem ručnog kreiranja Pod-ova

- `Pod`-ovi su potrošni resursi
- Ako se `Pod` obriše, Kubernetes ga neće automatski vratiti ako je kreiran direktno => Ručno kreiran `Pod` nije pogodan za produkcione aplikacije
- Potrebno je koristiti kontrolere koji održavaju željeni broj instanci
- Najčešće korišćen kontroler je `Deployment`

---

## Deployment

- `Deployment` opisuje aplikaciju koja treba stalno da radi
- Definiše:
  - koji image se koristi
  - koliko replika treba da postoji
  - kako se biraju Pod-ovi
  - kako se izvršava ažuriranje
- `Deployment` kreira `ReplicaSet`
- `ReplicaSet` kreira i održava `Pod`-ove

---

## ReplicaSet

- `ReplicaSet` održava zadati broj Pod-ova
- Ako jedan Pod padne, kreira se novi
- Ako ima previše `Pod`-ova, višak se uklanja
- Uobičajeno se ne kreira direktno
- `Deployment` upravlja `ReplicaSet` resursima tokom životnog ciklusa aplikacije

---

## Deployment i ReplicaSet

- `ReplicaSet` odgovara na pitanje: koliko Pod-ova treba da postoji?
- `Deployment` odgovara na šire pitanje: koja verzija aplikacije treba da radi i kako se ažurira?
- `Deployment` kreira novi `ReplicaSet` kada se promeni opis `Pod`-a
- Stari `ReplicaSet` ostaje kao deo istorije ažuriranja
- Zato `Deployment` podržava:
  - rolling update
  - rollback
  - istoriju verzija
  - jednostavnije upravljanje aplikacijom

---

## Deployment primer

<style scoped>
pre { font-size: 0.62em; }
</style>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          ports:
            - containerPort: 80
```
---

## Labele i selektori

- Labela je par ključ-vrednost pridružen Kubernetes resursu, koristi se za grupisanje i pronalaženje resursa
- Selektor bira resurse na osnovu labela
- `Deployment` koristi selektor da pronađe `Pod`-ove kojima upravlja
- `Service` koristi selektor da pronađe `Pod`-ove ka kojima šalje saobraćaj

```yaml
labels:
  app: web
  environment: development
```

---

## Skaliranje

- Broj replika se može promeniti izmenom opisa `Deployment`-a u manifest fajla
- Može se promeniti i komandom:

```bash
kubectl scale deployment web --replicas=5
kubectl get pods
```

- Potrebno je praviti razliku između horizontalnog i vertikalnog skaliranje:
  - Horizontalno skaliranje povećava broj instanci aplikacije
  - Vertikalno skaliranje povećava CPU ili memoriju jedne instance

---

## Ažuriranje aplikacije

- `Deployment` podržava postepeno ažuriranje aplikacije
- Nova verzija `Image`-a zamenjuje staru bez potpunog gašenja sistema
- Ako nova verzija ima problem, moguće je vratiti prethodnu

```bash
kubectl set image deployment/web nginx=nginx:1.27
kubectl rollout status deployment/web
kubectl rollout history deployment/web
kubectl rollout undo deployment/web
```

---

## Service

- `Pod`-ovi su prolazni i dobijaju dinamičke IP adrese
- `Service` komponenta obezbeđuje stabilnu mrežnu adresu za grupu `Pod`-ova
- `Service` koristi selektor da pronađe odgovarajuće `Pod`-ove
- Klijenti pristupaju `Service`-u, a ne direktno `Pod`-ovima
- Kubernetes zatim prosleđuje saobraćaj ka jednom od odgovarajućih `Pod`-ova
- Osnovni tipovi: `ClusterIP`, `NodePort`, `LoadBalancer`, `ExternalName`

---

## Kako Service radi

- `Service` ima stabilno ime i IP adresu unutar klastera
- Selektor pronalazi `Pod`-ove na osnovu labela
- Ako se `Pod` ugasi i nastane novi `Pod`, `Service` se ne menja
- Drugi `Pod`-ovi mogu koristiti DNS ime `Service`-a

```text
adminer Pod -> mysql Service -> mysql Pod
```

---

## ClusterIP

- `ClusterIP` je podrazumevani tip `Service`-a
- Servis je dostupan samo unutar klastera
- Koristi se za internu komunikaciju između aplikacija

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
```

---

## NodePort

- `NodePort` otvara port na svakom čvoru klastera
- Omogućava pristup servisu spolja, preko adrese čvora
- Koristan je u lokalnom i test okruženju
- U produkciji se češće koristi `LoadBalancer` ili `Ingress`
- Aplikacije su dostupne na portu `nodePort` (30000 - 32767)

```yaml
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
```

---

## LoadBalancer

- `LoadBalancer` traži od cloud platforme da napravi spoljašnji `Load Balancer`
- Primeri:
  - Google Kubernetes Engine
  - Azure Kubernetes Service
  - Amazon Elastic Kubernetes Service
- U lokalnom okruženju često zahteva dodatne alate

---

## Ingress

- `Ingress` upravlja HTTP i HTTPS pristupom aplikacijama
- Omogućava rutiranje po domenima i putanjama
- Za rad je potreban `Ingress Controller`
- Često se koristi za:
  - više aplikacija iza jedne javne adrese
  - TLS sertifikate
  - centralizovana pravila rutiranja

---

## Ingress primer

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
spec:
  rules:
    - host: web.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

---

## Namespace

- `Namespace` omogućava logičko razdvajanje resursa unutar klastera
- Koristi se za:
  - razvojna, test i produkciona okruženja
  - različite timove
  - izolaciju konfiguracije i prava pristupa
- Neki podrazumevani:
  - `default`
  - `kube-system`
  - `kube-public`

---

## Namespace komande

```bash
kubectl get namespaces
kubectl create namespace development
kubectl get pods -n development
kubectl apply -f deployment.yaml -n development
```

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development
```

---

## Konfiguracija

- Aplikaciji su često potrebni parametri koji ne treba da budu ugrađeni u image
- Primeri:
  - adresa baze
  - naziv okruženja
  - feature flag vrednosti
  - putanje i sl.
- Kubernetes za ovo koristi `ConfigMap`

---

## ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  ENVIRONMENT: development
  DATABASE_HOST: mysql
```

```yaml
envFrom:
  - configMapRef:
      name: app-config
```

---

## Secrets

- `Secret` čuva osetljive podatke
- Primeri:
  - lozinke
  - tokeni
  - privatni ključevi
  - API ključevi
- Vrednosti su Base64 kodirane, ali to nije isto što i enkripcija
- U produkciji je važno podesiti enkripciju podataka i kontrolu pristupa

---

## Secret primer

```bash
kubectl create secret generic db-secret \
  --from-literal=MYSQL_ROOT_PASSWORD=root
```

```yaml
env:
  - name: MYSQL_ROOT_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: MYSQL_ROOT_PASSWORD
```

---

## Storage problem

- Kontejneri su prolazni
- `Pod` može biti obrisan i ponovo kreiran na drugom čvoru
- Podaci zapisani direktno u fajl sistem kontejnera nestaju sa kontejnerom
- Za baze podataka potreban je trajno rešenje
- Kubernetes koristi `volume` mehanizme za povezivanje `Pod`-ova sa skladištem

---

## Volume

- `Volume` predstavlja direktorijum dostupan kontejnerima u `Pod`-u
- Životni ciklus `volume`-a vezan je za Pod, osim ako koristi trajno skladište
- Više kontejnera u istom `Pod`-u može deliti isti `volume`
- Primeri volume tipova:
  - `emptyDir`
  - `configMap`
  - `secret`
  - `persistentVolumeClaim`

---

## PersistentVolume

- `PersistentVolume`, skraćeno `PV`, predstavlja konkretan storage resurs
- Može biti lokalni disk, mrežni disk ili cloud storage
- `PersistentVolumeClaim`, skraćeno `PVC`, je zahtev aplikacije za storage
- `Pod` obično ne koristi `PV` direktno
- Pod koristi `PVC`, a Kubernetes ga povezuje sa odgovarajućim `PV` resursom

---

## PVC primer

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

---

## Korišćenje PVC-a u Pod-u

<style scoped>
pre { font-size: 0.62em; }
</style>

```yaml
spec:
  containers:
    - name: mysql
      image: mysql:8
      env:
        - name: MYSQL_ROOT_PASSWORD
          value: root
      volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
  volumes:
    - name: mysql-data
      persistentVolumeClaim:
        claimName: mysql-data
```

---

## StorageClass

- `StorageClass` opisuje način na koji se storage dinamički kreira
- U cloud okruženju može se automatski napraviti disk za PVC
- U lokalnim okruženjima zavisi od alata koji se koristi
- Omogućava da aplikacija zatraži storage bez poznavanja fizičke infrastrukture

```bash
kubectl get storageclass
kubectl get pv
kubectl get pvc
```

---

## StatefulSet

- `Deployment` je pogodan za stateless aplikacije
- Za aplikacije kojima je bitan stabilan identitet koristi se `StatefulSet`
- Primeri:
  - baze podataka
  - distribuirani sistemi
- `StatefulSet` obezbeđuje predvidljiva imena `Pod`-ova i stabilnije povezivanje sa storage-om

---

## Zdravlje aplikacije

- Kubernetes može proveravati da li je aplikacija živa i spremna
  - `livenessProbe` proverava da li aplikaciju treba restartovati
  - `readinessProbe` proverava da li `Pod` može da prima saobraćaj
  - `startupProbe` pomaže aplikacijama koje se dugo pokreću
-  Ovime se smanjuje potreba za ručnim intervencijama i sprečavaju slanje saobraćaja ka nespremnim instancama

---

## Probe primer

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Probe primer

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    test: liveness
  name: liveness-exec
spec:
  containers:
  - name: liveness
    image: registry.k8s.io/busybox:1.27.2
    args:
    - /bin/sh
    - -c
    - touch /tmp/healthy; sleep 30; rm -f /tmp/healthy; sleep 600
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      initialDelaySeconds: 5
      periodSeconds: 5
```
---

## Resources

- Kontejnerima se mogu zadati CPU i memorijska ograničenja
- `requests` definiše minimum koji se koristi prilikom raspoređivanja
- `limits` definiše maksimalnu dozvoljenu potrošnju
- Bez ovih podešavanja jedan Pod može potrošiti previše resursa

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

---

## Autoscaling

- `HorizontalPodAutoscaler`, skraćeno `HPA`, automatski menja broj replika
- Najčešće se zasniva na CPU ili memoriji
- Može koristiti i custom metrike

```bash
kubectl autoscale deployment web \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

```bash
kubectl get hpa
```

---

## Job i CronJob

- `Job` pokreće zadatak koji treba uspešno da se završi
- `CronJob` pokreće zadatak nakon svakog intervala
- Koriste se za:
  - migracije
  - batch obradu
  - periodično čišćenje podataka
  - zakazane izveštaje

```bash
kubectl get jobs
kubectl get cronjobs
```

---

## Primer Job-a

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: hello
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: hello
          image: busybox
          command: ["sh", "-c", "echo Hello Kubernetes"]
```

---

## Helm

- `Helm` je paket menadžer za Kubernetes
- Aplikacije se pakuju kao `chart`
- `Chart` sadrži šablone Kubernetes manifest fajlova
- Vrednosti se menjaju preko `values.yaml`
- Koristan je za instalaciju gotovih sistema kao što su PostgreSQL, Redis, Prometheus ili Grafana

```bash
helm install my-release bitnami/nginx
helm list
```

---

## Lokalno okruženje

- Za vežbu se može koristiti lokalni Kubernetes klaster
- Česti alati:
  - Docker Desktop Kubernetes
  - Minikube
  - Kind
  - k3d
- Lokalno okruženje je dovoljno za učenje osnovnih koncepata
- Produkciona okruženja dodaju sigurnost, monitoring, backup i ozbiljnije mrežne zahteve

---

## Tipičan tok rada

```bash
docker build -t my-app:1.0 .
kubectl create namespace demo
kubectl apply -f deployment.yaml -n demo
kubectl apply -f service.yaml -n demo
kubectl get all -n demo
kubectl logs deployment/my-app -n demo
kubectl delete namespace demo
```

---

## Debug komande

```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl logs deployment/<deployment-name>
kubectl exec -it <pod-name> -- /bin/sh
kubectl get events --sort-by=.metadata.creationTimestamp
```

- `describe` je posebno koristan kada Pod ne može da se pokrene
- `events` često otkrivaju probleme sa image-om, resursima ili storage-om

---

## Česti problemi

- `ImagePullBackOff`
  - image ne postoji, pogrešan tag ili nema pristupa registru
- `CrashLoopBackOff`
  - aplikacija se pokrene pa brzo padne
- `Pending`
  - nema dovoljno resursa ili storage nije dostupan
- `Service` ne radi
  - selector ne odgovara label-ima Pod-ova
- `PVC` ostaje `Pending`
  - nema odgovarajućeg `PV`-a ili `StorageClass`-a

---

## Šta Kubernetes ne rešava sam

- Kubernetes nije zamena za dobar dizajn aplikacije
- Ne rešava automatski:
  - loše napisanu aplikaciju
  - migracije baze bez plana
  - backup i restore strategiju
  - monitoring i alerting
  - sigurnost image fajlova
  - pravilno upravljanje tajnama
- Kubernetes daje mehanizme, ali ne donosi sve operativne odluke umesto tima
