# Bordereau SOCADEL

Bordereau intelligent de collecte de numéros WhatsApp, réalisé par **NEXT LTD**
(Numeric Export Technologies) pour **SOCADEL** — Société Camerounaise
d'Electricité.

## Le problème que ce système résout

Des agents de terrain parcourent des itinéraires de relève pour faire abonner
les clients SOCADEL à la réception de leur facture par WhatsApp. Ils travaillent
sur papier ; c'est le superviseur qui saisit leur production dans
l'application, agent par agent, jour par jour.

Une déclaration de superviseur n'est pas une vérité : quand un client s'abonne
réellement, son numéro et son contrat remontent au référentiel SOCADEL via le
chatbot. Le système confronte alors chaque déclaration à ce référentiel — et
c'est ce recoupement, pas la déclaration, qui détermine ce qui sera payé à
l'agent.

## La journée type

| Étape | Écran | Ce qui se passe |
|---|---|---|
| 1. Briefing | **Affectations** | L'agent se présente ; le superviseur note les itinéraires qu'il lui confie. L'application crée aussitôt une ligne de bordereau par client concerné. |
| 2. Départ | **Affectations** | Le superviseur imprime le bordereau papier de l'itinéraire (PDF), que l'agent emporte. |
| 3. Retour | **Bordereau** | Le superviseur saisit, ligne à ligne ou en lot, ce que l'agent a réalisé. Il peut aussi importer un fichier rempli. |
| 4. Contrôle | **Bordereau** | Un clic confronte les déclarations au référentiel : confirmé, infirmé, ou contrat introuvable. |
| 5. Suivi | **Tableau de bord** | KPI, courbe d'évolution, couverture des itinéraires et fiabilité par agent. |

## Démarrage

### Prérequis

- Python 3.11 ou plus
- Node.js 20 ou plus, avec pnpm
- PostgreSQL 16 (ou Docker)

### Base de données

```bash
docker compose up -d db
```

### Backend

```bash
cd backend-bordereau-socadel
python -m venv .venv && . .venv/Scripts/activate   # Linux/macOS : . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# Schéma, compte superviseur et agents d'essai
python scripts/seed.py --tout

# Référentiel clients (plus de 400 000 lignes : comptez quelques minutes)
python scripts/seed.py --referentiel ../Documents/bordereau2.xlsx

uvicorn bordereau.main:app --app-dir src --reload --port 8000
```

L'API est documentée sur <http://localhost:8000/docs>.

### Frontend

```bash
cd frontend-bordereau-socadel
pnpm install
cp .env.example .env.local
pnpm dev
```

Le back-office est sur <http://localhost:3000>.

### Identifiants de connexion

| Profil | Identifiant | Mot de passe |
|---|---|---|
| Super utilisateur, NEXT LTD | `sudo` | `Ngaoundal-Kribi-88` |
| Administrateur, SOCADEL | `admin` | `Bandjoun-Maroua-77` |
| Superviseur | `superviseur` | `Ngaoundere-Sud-2026` |
| Agent de terrain | `ag001` | `Terrain-Essos-2026` |

Les nouveaux utilisateurs s'inscrivent eux-mêmes ; un responsable approuve.

Le [guide pratique](./GUIDE-PRATIQUE.md) déroule chaque flux pas à pas.

Ils viennent de `SUPERVISEUR_IDENTIFIANT` et `SUPERVISEUR_MOT_DE_PASSE` dans
`.env`. **À changer avant toute mise en production**, de même que `SECRET_KEY` :

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Structure du dépôt

```
bordereau-socadel/
├── backend-bordereau-socadel/     API FastAPI, clean architecture
├── frontend-bordereau-socadel/    Back-office Next.js
├── Documents/                     Classeurs sources (hors dépôt)
├── public/                        Logo de référence
└── docker-compose.yml
```

## Documents

Les deux documents sont générés depuis le dépôt, pas rédigés à la main :

```bash
cd backend-bordereau-socadel
python scripts/generer_rapport.py   # dossier de conception, 21 pages + UML
python scripts/generer_guide.py     # guide pratique, depuis GUIDE-PRATIQUE.md
```

Ils atterrissent dans `Documents/`.

Chaque projet a son propre README détaillant son architecture :
[backend](./backend-bordereau-socadel/README.md) ·
[frontend](./frontend-bordereau-socadel/README.md).

## Vérifications

```bash
cd backend-bordereau-socadel && python -m pytest      # 96 tests
cd frontend-bordereau-socadel && pnpm typecheck && pnpm build
```

## Charte graphique

Le bleu **`#1A76B9`** est échantillonné sur `public/LOGO_SOCADEL_CM.jpg`. Il
porte l'interface, les documents PDF exportés et les icônes d'application —
l'éclair du logotype, isolé et posé sur un carré bleu.

Les couleurs des graphiques ont été validées pour la déficience de vision des
couleurs et le contraste, sur les deux surfaces réellement utilisées : voir
`frontend-bordereau-socadel/src/features/analytics/ui/palette.ts`.
