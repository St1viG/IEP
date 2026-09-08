# Modifikacija na odbrani

Na odbrani se traži **jedna izmena uživo**, i ona je uslov za bodove: konačan
rezultat se množi procentom testova koji prođu **posle** izmene. Znači dva
pravila, oba jednako važna — uradi traženo, i **ne slomi ništa postojeće**.

Bodovanje: 30 osnovni kod + 15 Kubernetes + 15 blockchain, maksimum 60, pomnoženo
procentom prolaznosti nakon modifikacije.

## Postupak, isti za svaku izmenu

```sh
cp src/director.py src/director.py.bak          # najbrži undo

# 1. izmeni fajl
# 2. rebuild samo tog servisa, par sekundi:
docker compose -f deploy/deployment.yaml up -d --build director

# 3. proveri novu rutu:
sh deploy/proveri.sh director /nova_ruta        # Windows: deploy\proveri.cmd

# 4. na kraju: postojeće ponašanje mora ostati netaknuto
python scenario.py
```

Gde šta živi u ovom projektu:

| Traži se | Fajl | Dekorator |
|---|---|---|
| statistika nad imovinom, izveštaj | `src/director.py` | `@role_check("director")` |
| pretraga, čitanje imovine | `src/employee.py` | `@role_check("employee")` |
| statistika nad pending zahtevima | `src/director.py` (Redis) | `@role_check("director")` |
| bilo šta o korisnicima | `src/authentication.py` | `@jwt_required()` |

U `director.py` je kolekcija već otvorena kao `assets`, Redis kao `redis`, a
`Configuration.REDIS_ORDERS` je ime hash-a sa zahtevima. U `employee.py` isto,
plus `serialize(asset)` koji dokument pretvara u oblik iz specifikacije.

## Tri zamke koje nose poene

1. **„po kategoriji" ⇒ obavezan `$unwind`.** `categories` je lista; bez `$unwind`
   grupišeš po celoj listi umesto po pojedinačnoj kategoriji.
2. **„ukupno" ⇒ bez `$unwind`.** Sa njim bi imovina u dve kategorije bila
   brojana dvaput. Grupiši sa `"_id": None`.
3. **„prodatih" ⇒ `$match` na `{"selling_date": {"$exists": True}}`.** Bez toga
   sabiraš i nepostojeće prodajne cene.

I jedno pravilo iznad svih: **filtriraj upitom, ne Python petljom.** Asistenti
skidaju bodove za `for` petlju tamo gde je moguć `aggregate` ili SQLAlchemy upit.
`/report` mora ići kroz aggregation framework — naš ide. Sirov SQL nije dozvoljen,
mora ORM — naš `authentication.py` nigde ne piše SQL string.

Jedini legitiman izuzetak je Redis: nema upitni jezik, pa je petlja jedini način.
To reci naglas pre nego što te pitaju.

## Gotovi obrasci

Svi u stilu ostatka projekta (PEP 8, `jsonify`, `role_check`).

### Agregacija po kategoriji — „broj kupljenih asseta po kategoriji"

```python
@application.route("/bought", methods=["GET"])
@role_check("director")
def bought():
    pipeline = [
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "bought": {"$sum": 1}}},
        {"$project": {"_id": 0, "category": "$_id", "bought": 1}},
        {"$sort": {"category": 1}},
    ]

    return jsonify(statistics=list(assets.aggregate(pipeline)))
```

Varijante iste stvari, menja se samo jedan red:

- **prodatih** po kategoriji → dodaj `{"$match": {"selling_date": {"$exists": True}}}` na početak
- **još u vlasništvu** → isti `$match`, ali `"$exists": False`
- **suma prodajnih cena** → `{"$sum": "$selling_price"}` umesto `{"$sum": 1}`
- **prosečna kupovna cena** → `{"$avg": "$buying_price"}`
- **najskuplja kupovina** → `{"$max": "$buying_price"}`
- **spisak imena po kategoriji** → `{"$push": "$name"}`
- **profit po kategoriji** → dva `$sum` pa `{"$subtract": ["$earned", "$spent"]}` u `$project`

### Ukupan broj, bez kategorija — „ukupan broj prodatih asseta"

Bez `$unwind`, i izvuci čist broj iz liste od jednog elementa:

```python
@application.route("/sold_total", methods=["GET"])
@role_check("director")
def sold_total():
    pipeline = [
        {"$match": {"selling_date": {"$exists": True}}},
        {"$group": {"_id": None, "sold": {"$sum": 1}}},
    ]

    result = list(assets.aggregate(pipeline))

    return jsonify(sold=result[0]["sold"] if result else 0)
```

### Filtriranje kroz gubitak — „kategorije koje posluju sa gubitkom"

`$match` posle `$group` filtrira po izračunatoj vrednosti:

```python
    pipeline = [
        {"$unwind": "$categories"},
        {
            "$group": {
                "_id": "$categories",
                "spent": {"$sum": "$buying_price"},
                "earned": {"$sum": {"$cond": [SOLD, "$selling_price", 0]}},
            }
        },
        {"$match": {"$expr": {"$lt": ["$earned", "$spent"]}}},
        {"$project": {"_id": 0, "category": "$_id", "spent": 1, "earned": 1}},
    ]
```

`SOLD` već postoji u `director.py`.

### Parametar u putanji ili upitu

```python
@application.route("/by_category/<category>", methods=["GET"])
@role_check("director")
def by_category(category):
    return jsonify(count=assets.count_documents({"categories": category}))
```

```python
from flask import request

    start = request.args.get("from")
    end = request.args.get("to")

    match = {}

    if start is not None:
        match["buying_date"] = {"$gte": parse_iso(start)}
    if end is not None:
        match.setdefault("buying_date", {})["$lte"] = parse_iso(end)
```

`parse_iso` postoji u `employee.py`; u `director.py` ga prekopiraj ili uvezi.

### Ugnježdeno polje — „broj asseta po državi (`info.geo.country`)"

```python
    pipeline = [
        {"$group": {"_id": "$info.geo.country", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "country": "$_id", "count": 1}},
        {"$sort": {"country": 1}},
    ]
```

### Redis — „broj zahteva na čekanju po tipu"

Petlja je ovde ispravna, Redis nema upitni jezik:

```python
@application.route("/pending_count", methods=["GET"])
@role_check("director")
def pending_count():
    counts = {"BUY": 0, "SELL": 0}

    for value in redis.hgetall(Configuration.REDIS_ORDERS).values():
        counts[json.loads(value)["order_type"]] += 1

    return jsonify(statistics=[{"order_type": k, "count": v} for k, v in counts.items()])
```

### SQLAlchemy — „broj korisnika po ulozi"

ORM, nikad string SQL. U `src/authentication.py`:

```python
from models import Role, User, UserRole, database


@application.route("/users_per_role", methods=["GET"])
@jwt_required()
def users_per_role():
    rows = (
        database.session.query(Role.name, database.func.count(UserRole.user_id))
        .join(UserRole, UserRole.role_id == Role.id)
        .group_by(Role.name)
        .all()
    )

    return jsonify(statistics=[{"role": name, "count": count} for name, count in rows])
```

### Nova validacija pri upisu

Uvek **u redosledu iz specifikacije**, i vrati na prvoj grešci. Npr. „lozinka mora
imati bar jednu cifru i jedno veliko slovo", u `register` posle postojeće provere
dužine:

```python
    if not any(character.isdigit() for character in password) or not any(
        character.isupper() for character in password
    ):
        return error("Invalid password.")
```

Ako se traži novo polje (npr. broj telefona), dodaj ga u `missing_field(...)`
listu **na mesto koje zadatak traži**, u `models.py` kao `database.Column`, i ne
zaboravi da migracija kreira tabele iz `models.py` — `docker compose ... up -d
--build migration` posle izmene modela, na praznoj bazi.

## Pred kraj

Kada izmena radi, pusti `python scenario.py` još jednom. Postojeće ponašanje je
ono što množi bodove — nova ruta vredi mnogo manje od devet koje već rade.
