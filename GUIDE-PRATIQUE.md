# Guide pratique — suivre les flux pas à pas

Ce guide se suit dans l'ordre, écran par écran. Chaque étape indique ce que
vous faites, ce que le système fait derrière, et comment vérifier que c'est
bien arrivé.

## Démarrer

```bash
# 1. La base
docker compose up -d db

# 2. L'API — port 8001, car 8000 est occupé par votre projet Django
cd backend-bordereau-socadel
python -m uvicorn bordereau.main:app --app-dir src --reload --port 8001

# 3. Le back-office
cd frontend-bordereau-socadel
pnpm dev
```

| | |
|---|---|
| Back-office | <http://localhost:3000> |
| API et sa documentation | <http://localhost:8001/docs> |

Si la base est vierge :

```bash
cd backend-bordereau-socadel
python scripts/seed.py --tout                              # schéma, agents, comptes
python scripts/seed.py --referentiel ../Documents/bordereau2.xlsx   # 425 920 clients
```

## Les trois connexions

| Acteur | Identifiant | Mot de passe | Ce qu'il voit |
|---|---|---|---|
| **Administrateur** | `admin` | `Admin@2026` | Tout, sans restriction. Seul à gérer les comptes. |
| **Superviseur** | `superviseur` | `Socadel@2026` | Son périmètre. Pilote les agents et le bordereau. |
| **Agent de terrain** | `ag001` | `Terrain@2026` | Sa seule production. Consultation uniquement. |

> Ces mots de passe sont ceux de la mise en route. Chaque titulaire doit les
> remplacer à sa première connexion, et `SECRET_KEY` doit être régénérée avant
> toute mise en production :
> `python -c "import secrets; print(secrets.token_urlsafe(48))"`

---

## Flux 1 — Le briefing du matin

**Vous êtes le superviseur. L'agent se présente et vous donne ses itinéraires.**

1. Connectez-vous avec `superviseur`. Vous arrivez **directement sur
   Affectations** — pas sur le tableau de bord. C'est voulu : c'est le premier
   geste de votre journée.

2. Choisissez l'agent dans la liste déroulante. Seuls les agents **actifs**
   y figurent.

3. Dans le champ de recherche, tapez un code d'itinéraire — essayez `42422`
   (CSC_ESSOS, 25 clients) ou `118194` (CSC_BANDJOUN, 25 clients). La recherche
   part à partir de deux caractères.

4. Cliquez sur le résultat pour l'ajouter. **Répétez pour chaque itinéraire**
   que l'agent vous annonce : un bon collecteur en reçoit plusieurs.

5. Vérifiez la date de travail, ajoutez une consigne si besoin, puis
   **Affecter et générer le bordereau**.

**Ce qui se passe derrière.** Une transaction unique crée l'affectation *et*
une ligne de bordereau par client de chaque itinéraire, triées par référence
géographique — c'est-à-dire dans l'ordre de marche réel des maisons. Si
quoi que ce soit échoue, rien n'est écrit.

**Comment vérifier.** Le bandeau de confirmation annonce le nombre de lignes
créées. Allez ensuite sur **Bordereau** : elles y sont, toutes au statut
« À traiter ».

### Ajouter des itinéraires plus tard

L'agent revient en cours de journée avec une tournée supplémentaire ?
Recommencez simplement le flux 1 avec le même agent. Les affectations
s'accumulent, ses chiffres se mettent à jour. La seule chose interdite est
d'affecter **deux fois le même itinéraire au même agent le même jour** —
sinon sa production serait comptée en double. L'API renvoie alors un conflit.

---

## Flux 2 — Imprimer le bordereau papier

**Toujours superviseur. L'agent part sur le terrain.**

Deux chemins :

- **Depuis l'écran d'affectation** : le bandeau de confirmation propose
  « Imprimer le bordereau » pour chaque itinéraire.
- **Depuis l'écran Itinéraires** : recherchez le code, puis « Bordereau
  terrain (PDF) ».

Pour **toute la journée d'un agent en un seul document** :

```
GET /api/v1/itineraires/journee/{agent_id}/bordereau-terrain.pdf?date_travail=AAAA-MM-JJ
```

**Ce que vous obtenez.** Un PDF calqué sur `Documents/bordereau.xlsx / Feuil3` :

- titre `CAMPAGNE DE COLLECTE DE NUMERO WHATSAPP`, centré ;
- bandeau `ITINERAIRE | code | Total client | n | OK/MRA`, plus l'agent, la
  date et la pagination ;
- colonnes `REF GEO | METER_NO | NOMS | CONTRAT | RAPPORT` ;
- **la colonne RAPPORT est vide**, cernée d'un trait bleu franc : c'est là que
  l'agent écrit le numéro relevé ;
- trois lignes vierges en fin de bloc, pour les clients rencontrés qui ne
  figurent pas encore au référentiel ;
- le logo SOCADEL en filigrane et en en-tête.

Un bloc par itinéraire, enchaînés : l'agent part avec une seule liasse.

---

## Flux 3 — Saisir la production au retour

**Superviseur, le soir, bordereau papier en main.**

### Ligne par ligne

1. Allez sur **Bordereau**. Filtrez si besoin — par date, par statut, ou
   cherchez un nom, un contrat, un compteur.
2. Triez sur **Réf. géo** pour retrouver l'ordre du papier.
3. Cliquez **Saisir** sur une ligne.
4. Choisissez le résultat du passage, entrez le numéro relevé, l'origine, une
   remarque éventuelle. Enregistrez.

**La règle à connaître.** Un client déclaré **Abonné** exige le numéro
collecté. Sans lui, l'enregistrement est refusé — le formulaire le signale, et
l'API le refuserait de toute façon. Vous pouvez saisir le numéro sans
indicatif (`677889900`), il sera normalisé en `+237677889900`.

### En lot

Cochez plusieurs lignes, choisissez un statut dans la barre bleue, cliquez
**Appliquer**. Les lignes que la règle ci-dessus refuse sont ignorées, et le
message vous dit combien restent à saisir individuellement.

### Par import de fichier

1. Écran **Import / Export** → **Télécharger le modèle (.xlsx)**.
2. Le fichier rempli, revenez et déposez-le. Un **aperçu s'ouvre** : lignes
   retenues, lignes rejetées, et le motif de chaque rejet. **Rien n'est encore
   écrit.**
3. Confirmez. L'écriture se fait alors en une transaction unique.

---

## Flux 4 — Vérifier auprès du référentiel

**C'est le cœur du dispositif.**

Sur l'écran **Bordereau**, cliquez **Vérifier auprès du référentiel**. La
vérification porte sur le périmètre actuellement filtré.

Chaque ligne déclarée reçoit un verdict :

| Déclaration | État du référentiel | Verdict | Payable |
|---|---|---|---|
| Abonné | Contrat absent du référentiel | Introuvable | Non |
| Abonné | Pas abonné WhatsApp | **Infirmé** | Non |
| Abonné | Abonné, mais autre numéro | **Infirmé** | Non |
| Abonné | Abonné, numéro concordant | **Confirmé** | **Oui** |
| Absent, refus… | Pas abonné | Confirmé | Non |
| Absent, refus… | Abonné au référentiel | Infirmé | Non |

**Pourquoi cela compte.** C'est ce recoupement, jamais la déclaration seule,
qui détermine ce qui sera payé. Il applique la recommandation de la
présentation NEXT : *« verser la prime uniquement sur les parcours menés
jusqu'à la confirmation finale »*.

**Ce que vous verrez aujourd'hui.** La base actuelle est une base de test :
aucun client n'y est `subscribed`. Tout abonnement déclaré ressort donc
**Infirmé**, et la fiabilité de l'agent tombe à 0 %. C'est le comportement
correct — il deviendra utile le jour où l'API MRA alimentera le vrai statut.

Corriger une ligne déjà vérifiée remet automatiquement son verdict à « Non
vérifié » : il faudra la re-confronter.

---

## Flux 5 — Suivre et exporter

**Tableau de bord** — cinq indicateurs avec leur variation, la courbe
d'évolution sur 7 / 14 / 30 / 90 jours, la répartition par statut, la
couverture des itinéraires et la performance de chaque agent.

La colonne **Fiabilité** du classement est la plus importante : c'est la part
des abonnements déclarés que le référentiel confirme. Un fort volume assorti
d'une fiabilité basse signale des déclarations qui ne se matérialisent pas.

**Exports** — les boutons CSV et PDF de l'écran Bordereau exportent
**exactement le périmètre affiché**, filtres compris. Le PDF porte le
filigrane et le titre centré. Au-delà de 50 000 lignes l'export est tronqué,
et l'interface vous le dit.

---

## Flux 6 — Gérer les agents

**Superviseur**, écran **Agents** : créer, modifier, retirer du service,
remettre en service. La photo de profil se dépose séparément et s'affiche en
aperçu avant que vous validiez le formulaire.

Le **matricule n'est pas modifiable** : tous les bordereaux passés le
référencent. Et un agent n'est **jamais supprimé** — « retirer du service »
le désactive, son historique reste intact puisqu'il fonde sa rémunération.

Cliquez **Voir le portefeuille** pour ouvrir ce que l'agent porte : ses
itinéraires, leur avancement, ses chiffres. C'est l'écran à ouvrir avant de
lui confier une tournée de plus.

---

## Flux 7 — L'agent consulte ses chiffres

**Connectez-vous avec `ag001` / `Terrain@2026`.**

Vous n'avez qu'une entrée de menu : **Mon espace**. Vous y voyez vos
itinéraires confiés avec leur avancement, et vos cinq chiffres — clients
confiés, démarchés, abonnements déclarés, confirmés, fiabilité.

**Essayez de sortir de votre périmètre**, c'est instructif : ajoutez
`?agent=<id d'un autre agent>` à l'URL de l'API. Vous obtiendrez vos propres
lignes, pas les siennes. Le filtre est réécrit avant d'atteindre la base — ce
n'est pas un contrôle qu'on peut oublier d'appeler.

Vous ne pouvez ni saisir, ni exporter, ni modifier quoi que ce soit.

---

## Flux 8 — L'administrateur ouvre les accès

**Connectez-vous avec `admin` / `Admin@2026`.**

Vous avez en plus l'entrée **Comptes**. Vous y ouvrez les accès des
superviseurs et des agents.

Pour un compte agent, vous devez **désigner l'agent de terrain rattaché** :
c'est ce rattachement qui délimite ce que le titulaire verra. Sans lui, le
système refuse la création — un compte agent sans périmètre verrait par
défaut la production de tous.

Vous pouvez aussi attribuer une **région** ou une **agence** à un superviseur
pour le territorialiser. Tant qu'aucune n'est définie, il voit tout le
national.

Une garde vous empêche de désactiver votre propre compte : vous vous
verrouilleriez dehors.

---

## Ce qui reste à faire

| Sujet | État |
|---|---|
| API de recoupement NEXT / MRA | Non ouverte. La vérification tourne sur la base de test. Un seul adaptateur restera à écrire. |
| Périmètres territoriaux | Le mécanisme existe et est testé, mais aucun superviseur n'en a. |
| Migrations Alembic | Configurées ; la révision initiale reste à générer avant production. |
| Mots de passe et `SECRET_KEY` | Valeurs de mise en route, à remplacer. |
