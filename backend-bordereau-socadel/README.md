# Backend — API Bordereau SOCADEL

FastAPI, PostgreSQL, clean architecture.

## La règle de dépendance

Les flèches ne pointent que vers l'intérieur. Le domaine ne connaît personne ;
l'infrastructure connaît tout le monde.

```
interfaces/  ──►  application/  ──►  domain/
     │                  ▲
     └──────────────────┼──── infrastructure/
                        │
              (implémente les ports)
```

| Couche | Contient | Ne connaît pas |
|---|---|---|
| `domain/` | Entités, objets-valeurs, règles métier | FastAPI, SQLAlchemy, Pydantic — rien du tout |
| `application/` | Cas d'usage, ports, DTO | Aucun framework ; seulement le domaine |
| `infrastructure/` | PostgreSQL, bcrypt, JWT, openpyxl, reportlab | — |
| `interfaces/` | Routes HTTP, schémas Pydantic | La base de données |

Cette discipline est vérifiable : les couches `domain` et `application`
s'importent sur un interpréteur nu, sans une seule dépendance installée.

```bash
PYTHONPATH=src python -c "import bordereau.application.use_cases.collectes"
```

C'est elle aussi qui permet à la suite de tests d'exercer l'API HTTP complète
en remplaçant PostgreSQL par des doubles en mémoire (`tests/doubles.py`), sans
toucher une ligne de code de production.

## Arborescence

```
src/bordereau/
├── domain/                        Le cœur métier, sans dépendance
│   ├── entities/                  Client, LigneBordereau, Affectation…
│   ├── value_objects/             NumeroTelephone, ServiceNo, RefGeo…
│   ├── services/                  Règles transverses (vérification, performance)
│   ├── enums.py
│   └── errors.py
│
├── application/                   Orchestration
│   ├── ports/                     Protocoles que l'infrastructure implémente
│   ├── dto/                       Objets de transfert (pagination, filtres…)
│   └── use_cases/                 Une classe par intention métier
│       ├── auth/  collectes/  itineraires/
│       └── agents/  imports/  exports/  analytics/
│
├── infrastructure/                Adaptateurs concrets
│   ├── config/                    Réglages lus dans l'environnement
│   ├── db/                        Modèles ORM, mappers, repositories, migrations
│   ├── security/                  bcrypt, JWT, horloge
│   ├── files/                     Lecture Excel/CSV, exports PDF/CSV, modèle
│   └── container.py               Composition root
│
├── interfaces/http/               Exposition HTTP
│   ├── routers/  schemas/  deps.py  errors.py  api.py
│
└── main.py                        Point d'entrée ASGI
```

## Points de conception

**Le référentiel est la source de vérité.** `domain/services/verification_collecte.py`
porte la règle qui départage la déclaration du superviseur et l'état réel de
l'abonnement. Une ligne n'est payable que si elle est *à la fois* déclarée
abonnée et confirmée par le référentiel (`LigneBordereau.est_remuneree`).

**Affecter, c'est matérialiser.** `AffecterItineraires` crée l'affectation *et*
une ligne de bordereau par client de l'itinéraire, en recopiant les données du
client sur la ligne : le bordereau reste lisible tel qu'il a été émis, même si
le référentiel évolue ensuite.

**Un seul objet de filtre.** `FiltreBordereau` sert le listing paginé, les
exports et les KPI. C'est ce qui garantit qu'un export contient exactement ce
que le superviseur voit à l'écran.

**Lecture et écriture séparées.** Les KPI ne chargent pas d'entités : le port
`RequetesAnalytiques` renvoie directement des DTO, traduits en agrégations SQL.
Agréger 400 000 lignes en mémoire n'aurait pas de sens.

**Le volume est une contrainte de conception.** Insertions par paquets,
chargement des clients en lot avant vérification, pagination bornée à 200
lignes, exports plafonnés à 50 000 lignes avec un en-tête `X-Export-Tronque`
qui prévient le frontend.

## Commandes

```bash
pip install -e ".[dev]"

uvicorn bordereau.main:app --app-dir src --reload --port 8000

python -m pytest                 # suite complète
python -m pytest tests/unit      # domaine seul, très rapide

ruff check src tests
mypy src

alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Script d'initialisation

```bash
python scripts/seed.py --tout                              # schéma + compte + agents
python scripts/seed.py --referentiel ../Documents/bordereau2.xlsx
```

Le référentiel est lu en flux et écrit par paquets de 5 000 : le classeur de
46 Mo n'est jamais chargé entièrement en mémoire. Les itinéraires sont déduits
des clients au passage, avec leur rattachement territorial.

## Modèle de données

| Table | Rôle |
|---|---|
| `clients` | Référentiel SOCADEL — la source de vérité. Issu de `bordereau2.xlsx`. |
| `itineraires` | Tournées de relève, déduites du référentiel. |
| `agents_terrain` | Collecteurs. Jamais supprimés : l'historique fonde leur rémunération. |
| `affectations` | Itinéraire confié à un agent pour une journée. Unicité (agent, itinéraire, jour). |
| `lignes_bordereau` | Déclarations du superviseur, avec leur verdict de vérification. |
| `utilisateurs` | Comptes du back-office. |
