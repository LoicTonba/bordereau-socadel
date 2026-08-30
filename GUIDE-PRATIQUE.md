# Guide pratique, suivre les flux pas à pas

Ce guide se suit dans l'ordre, écran par écran. Chaque étape indique ce que
vous faites, ce que le système fait derrière, et comment vérifier que c'est
bien arrivé.

## Démarrer

```bash
# 1. La base
docker compose up -d db

# 2. L'API, port 8001, car 8000 est occupé par votre projet Django
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

## Les quatre profils

| Profil | Chez qui | Portée | Ce qu'il fait de plus que le rang inférieur |
|---|---|---|---|
| **Super utilisateur** | NEXT LTD | Nationale, sans limite | Change les rôles, administre le référentiel, réinitialise n'importe quel mot de passe |
| **Administrateur** | SOCADEL | Nationale | Approuve les demandes d'accès, attribue les périmètres, réinitialise les mots de passe de ses équipes |
| **Superviseur** | SOCADEL, une agence | Son agence ou sa région | Affecte les itinéraires, saisit la production, gère le répertoire des agents |
| **Agent de terrain** | SOCADEL, sur le terrain | Sa propre production | Consulte ses chiffres. Rien d'autre |

**La règle qui gouverne tout** : chacun n'agit que sur les rangs
**strictement inférieurs** au sien. Un administrateur SOCADEL ne peut donc ni
créer un second administrateur, ni toucher au compte du super utilisateur NEXT
LTD qui lui a ouvert l'accès.

### Comptes de mise en route

| Profil | Identifiant | Mot de passe |
|---|---|---|
| Super utilisateur | `sudo` | `Ngaoundal-Kribi-88` |
| Administrateur | `admin` | `Bandjoun-Maroua-77` |
| Superviseur | `superviseur` | `Ngaoundere-Sud-2026` |
| Agent de terrain | `ag001` | `Terrain-Essos-2026` |

> Ces comptes servent à la mise en route. Chaque titulaire doit changer son
> mot de passe à la première connexion, et `SECRET_KEY` doit être régénérée
> avant toute mise en production :
> `python -c "import secrets; print(secrets.token_urlsafe(48))"`

---

## Flux 0 : S'inscrire sur la plateforme

**S'inscrire ne donne pas accès.** La plateforme porte le référentiel clients
de SOCADEL, plus de quatre cent mille noms et numéros : un accès ne s'obtient
pas en remplissant un formulaire. Le parcours compte quatre étapes.

1. **L'utilisateur s'inscrit** sur la page d'inscription. Il choisit son
   identifiant, son adresse électronique et **son propre mot de passe**, saisi
   deux fois. Une jauge lui indique en direct si le mot de passe tient : au
   moins dix caractères, sans mot courant ni reprise de son identifiant.

2. **Il confirme son adresse.** Un courriel part avec un lien valable trois
   jours. Tant qu'il ne l'a pas ouvert, la connexion est refusée, même avec le
   bon mot de passe.

3. **Un responsable approuve.** L'administrateur voit la demande dans l'écran
   Comptes, lui attribue un rôle et, s'il s'agit d'un superviseur, **un
   périmètre**. Sans périmètre, un superviseur verrait la production des 181
   agences : la plateforme refuse donc de le laisser passer.

4. **Le titulaire est prévenu** par un second courriel et peut se connecter.

### Où lire les courriels en développement

Aucun serveur SMTP n'est configuré par défaut : les messages sont **écrits sur
disque**, un fichier par courriel, dans `backend-bordereau-socadel/courriels/`.
Ouvrez le plus récent pour récupérer le lien de confirmation.

Pour envoyer réellement, renseignez `SMTP_HOTE`, `SMTP_PORT`,
`SMTP_UTILISATEUR` et `SMTP_MOT_DE_PASSE` dans `.env`. Rien d'autre ne change :
le code ne sait pas lequel des deux adaptateurs est en place.

### Mot de passe oublié

Deux chemins, selon la situation.

- **Le titulaire a encore accès à sa boîte** : il clique « Mot de passe
  oublié », reçoit un lien valable deux heures et choisit un nouveau mot de
  passe. La plateforme répond toujours la même chose, que l'adresse existe ou
  non : dire « adresse inconnue » offrirait un moyen simple de savoir qui a un
  compte.

- **Il n'y a plus accès, ou il faut débloquer tout de suite** : un responsable
  réinitialise pour lui depuis l'écran Comptes. La plateforme génère un mot de
  passe provisoire lisible au téléphone, sans I, l, O ni 0 pour éviter les
  confusions à l'oral. Ce mot de passe **n'est jamais écrit dans le courriel** :
  le responsable le communique de vive voix, et le titulaire doit le remplacer
  à sa prochaine connexion.

  La hiérarchie s'applique ici aussi : un superviseur ne réinitialise que ses
  agents, un administrateur ses superviseurs et ses agents, le super
  utilisateur tout le monde.

---

## Flux 0 bis : Se connecter en trois temps

La page de connexion ne demande pas l'identifiant en premier. Elle demande
d'abord **qui vous êtes**, puis **où vous êtes**, et seulement ensuite vos
identifiants. Ce n'est pas une formalité de plus, c'est ce qui permet d'ouvrir
la session sur le bon écran, déjà cadré.

1. **Choisissez votre profil.** Quatre cartes, du plus large au plus
   restreint : super utilisateur NEXT LTD, administrateur SOCADEL, superviseur,
   agent de terrain.

2. **Choisissez votre agence.** Le champ de recherche filtre les 181 agences du
   référentiel sur le nom, la division ou la direction : tapez `ESSOS` ou
   `DOUALA`. Les deux profils à portée nationale peuvent s'en tenir à
   « Portée nationale » ; un superviseur ou un agent doit désigner son agence.

3. **Saisissez vos identifiants.** Un bandeau rappelle le profil et l'agence
   retenus, avec un lien « Changer » si vous vous êtes trompé.

### Le raccourci du superviseur

À la troisième étape, le superviseur dispose d'un champ de plus :
**« Itinéraires annoncés par l'agent »**. L'agent connaît ses itinéraires par
cœur ; pendant qu'il les récite, notez les codes séparés par un espace ou une
virgule, par exemple `42422 42423`.

Vous n'arrivez alors pas sur l'écran d'affectation mais **directement sur le
bordereau, déjà filtré sur ces itinéraires**. Un bandeau bleu le rappelle en
haut du tableau, avec un lien « Tout afficher » pour en sortir. Sans code
saisi, la connexion se comporte comme avant.

Le chemin long reste évidemment disponible : se connecter, puis poser le filtre
à la main dans la barre du bordereau.

### Ce que le serveur vérifie

Trois contrôles, dans cet ordre.

| Contrôle | En cas d'écart |
|---|---|
| Le mot de passe | `401`, message indifférencié, on ne dit jamais si le compte existe |
| Profil déclaré = profil du compte | `409` et un message explicite, le mot de passe est déjà validé |
| Agence déclarée compatible avec le périmètre | `409`, avec le nom de l'agence attendue |

**Le profil et l'agence ne donnent aucun droit.** Le jeton porte le rôle du
compte, et l'ABAC rétrécit chaque requête au périmètre du compte, pas à
l'agence annoncée. Un superviseur de Ngaoundéré Sud qui déclarerait Kribi ne
verrait pas Kribi : il se verrait refuser l'entrée. C'est un confort de saisie,
doublé d'un garde-fou contre la session ouverte au mauvais poste.

---

## Flux 1 : Le briefing du matin

**Vous êtes le superviseur. L'agent se présente et vous donne ses itinéraires.**

1. Connectez-vous avec `superviseur`, profil **Superviseur**, agence
   **CSC_NGAOUNDERE SUD**, et laissez le champ des itinéraires vide. Vous
   arrivez **directement sur Affectations**, pas sur le tableau de bord.
   C'est voulu : c'est le premier
   geste de votre journée.

2. Choisissez l'agent dans la liste déroulante. Seuls les agents **actifs**
   y figurent.

3. Dans le champ de recherche, tapez un code d'itinéraire, essayez `42422`
   (CSC_ESSOS, 25 clients) ou `118194` (CSC_BANDJOUN, 25 clients). La recherche
   part à partir de deux caractères.

4. Cliquez sur le résultat pour l'ajouter. **Répétez pour chaque itinéraire**
   que l'agent vous annonce : un bon collecteur en reçoit plusieurs.

5. Vérifiez la date de travail, ajoutez une consigne si besoin, puis
   **Affecter et générer le bordereau**.

**Ce qui se passe derrière.** Une transaction unique crée l'affectation *et*
une ligne de bordereau par client de chaque itinéraire, triées par référence
géographique, c'est-à-dire dans l'ordre de marche réel des maisons. Si
quoi que ce soit échoue, rien n'est écrit.

**Comment vérifier.** Le bandeau de confirmation annonce le nombre de lignes
créées. Allez ensuite sur **Bordereau** : elles y sont, toutes au statut
« À traiter ».

### Ajouter des itinéraires plus tard

L'agent revient en cours de journée avec une tournée supplémentaire ?
Recommencez simplement le flux 1 avec le même agent. Les affectations
s'accumulent, ses chiffres se mettent à jour. La seule chose interdite est
d'affecter **deux fois le même itinéraire au même agent le même jour**, sinon sa production serait comptée en double. L'API renvoie alors un conflit.

---

## Flux 2 : Imprimer le bordereau papier

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

## Flux 3 : Saisir la production au retour

**Superviseur, le soir, bordereau papier en main.**

### Ligne par ligne

1. Allez sur **Bordereau**. Filtrez si besoin, par date, par statut, ou
   cherchez un nom, un contrat, un compteur.
2. Triez sur **Réf. géo** pour retrouver l'ordre du papier.
3. Cliquez **Saisir** sur une ligne.
4. Choisissez le résultat du passage, entrez le numéro relevé, l'origine, une
   remarque éventuelle. Enregistrez.

**La règle à connaître.** Un client déclaré **Abonné** exige le numéro
collecté. Sans lui, l'enregistrement est refusé, le formulaire le signale, et
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

## Flux 4 : Vérifier auprès du référentiel

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
correct, il deviendra utile le jour où l'API MRA alimentera le vrai statut.

Corriger une ligne déjà vérifiée remet automatiquement son verdict à « Non
vérifié » : il faudra la re-confronter.

---

## Flux 5 : Suivre et exporter

**Tableau de bord** : cinq indicateurs avec leur variation, la courbe
d'évolution sur 7 / 14 / 30 / 90 jours, la répartition par statut, la
couverture des itinéraires et la performance de chaque agent.

La colonne **Fiabilité** du classement est la plus importante : c'est la part
des abonnements déclarés que le référentiel confirme. Un fort volume assorti
d'une fiabilité basse signale des déclarations qui ne se matérialisent pas.

**Exports**, les boutons CSV et PDF de l'écran Bordereau exportent
**exactement le périmètre affiché**, filtres compris. Le PDF porte le
filigrane et le titre centré. Au-delà de 50 000 lignes l'export est tronqué,
et l'interface vous le dit.

---

## Flux 6 : Gérer les agents

**Superviseur**, écran **Agents** : créer, modifier, retirer du service,
remettre en service. La photo de profil se dépose séparément et s'affiche en
aperçu avant que vous validiez le formulaire.

Le **matricule n'est pas modifiable** : tous les bordereaux passés le
référencent. Et un agent n'est **jamais supprimé**, « retirer du service »
le désactive, son historique reste intact puisqu'il fonde sa rémunération.

Cliquez **Voir le portefeuille** pour ouvrir ce que l'agent porte : ses
itinéraires, leur avancement, ses chiffres. C'est l'écran à ouvrir avant de
lui confier une tournée de plus.

---

## Flux 7 : L'agent consulte ses chiffres

**Connectez-vous avec `ag001` / `Terrain@2026`.**

Vous n'avez qu'une entrée de menu : **Mon espace**. Vous y voyez vos
itinéraires confiés avec leur avancement, et vos cinq chiffres, clients
confiés, démarchés, abonnements déclarés, confirmés, fiabilité.

**Essayez de sortir de votre périmètre**, c'est instructif : ajoutez
`?agent=<id d'un autre agent>` à l'URL de l'API. Vous obtiendrez vos propres
lignes, pas les siennes. Le filtre est réécrit avant d'atteindre la base, ce
n'est pas un contrôle qu'on peut oublier d'appeler.

Vous ne pouvez ni saisir, ni exporter, ni modifier quoi que ce soit.

---

## Flux 8 : L'administrateur gouverne les accès

**Connectez-vous avec `admin`.**

Vous avez en plus l'entrée **Comptes**. Vous y voyez les demandes d'accès en
attente, et vous approuvez celles de vos superviseurs et de vos agents.

Pour un compte agent, vous devez **désigner l'agent de terrain rattaché** :
c'est ce rattachement qui délimite ce que le titulaire verra. Sans lui, le
système refuse la création, un compte agent sans périmètre verrait par
défaut la production de tous.

Vous pouvez aussi attribuer une **région** ou une **agence** à un superviseur
pour le territorialiser. Tant qu'aucune n'est définie, il voit tout le
national.

Deux gardes vous protègent : vous ne pouvez ni suspendre votre propre
compte, ni approuver quelqu'un au rang d'administrateur. La seconde n'est pas
une limitation arbitraire, c'est ce qui empêche une escalade de privilèges par
un compte compromis.

### Ce que seul le super utilisateur peut faire

Connectez-vous avec `sudo` pour voir la différence. Deux permissions de plus,
et elles engagent le fonctionnement de la plateforme, pas seulement son
exploitation :

- **changer le rôle d'un compte existant**, y compris promouvoir un
  administrateur ;
- **administrer le référentiel**, c'est-à-dire la source sur laquelle repose
  toute la vérification.

C'est la frontière entre exploiter la plateforme, ce que fait SOCADEL, et en
répondre, ce que fait NEXT LTD.

---

## Ce qui reste à faire

| Sujet | État |
|---|---|
| API de recoupement NEXT / MRA | Non ouverte. La vérification tourne sur la base de test. Un seul adaptateur restera à écrire. |
| Périmètres territoriaux | Le mécanisme est en place et un superviseur sans périmètre est bloqué. Reste à attribuer les 181 agences aux superviseurs réels. |
| Migrations Alembic | Configurées ; la révision initiale reste à générer avant production. |
| Mots de passe et `SECRET_KEY` | Valeurs de mise en route, à remplacer. |
