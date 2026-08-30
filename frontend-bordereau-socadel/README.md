# Frontend — Back-office Bordereau SOCADEL

Next.js 16 (App Router), React 19, Tailwind v4, TanStack Query, Recharts.

## Organisation

La même règle de dépendance que le backend, transposée au découpage par
fonctionnalité : `app/` ne fait que du routage, la logique vit dans `features/`.

```
src/
├── app/                          Routage uniquement — pages très fines
│   ├── (auth)/login/             Écran de connexion
│   ├── (dashboard)/              Écrans authentifiés, sous la coquille
│   │   ├── affectations/         Premier écran après connexion
│   │   ├── dashboard/  bordereau/  itineraires/  agents/  imports/
│   ├── layout.tsx  providers.tsx
│
├── core/                         Noyau partagé, sans dépendance UI
│   ├── domain/types.ts           Types miroir du contrat d'API
│   └── domain/statuts.ts         Vocabulaire et couleurs des statuts
│
├── features/                     Une tranche par fonctionnalité
│   └── <feature>/
│       ├── infrastructure/       Appels HTTP
│       ├── application/          Hooks React Query, contexte
│       └── ui/                   Composants de l'écran
│
├── infrastructure/
│   ├── http/client.ts            Client HTTP unique
│   └── storage/session.ts        Persistance du jeton
│
├── shared/                       Design system et utilitaires
│   ├── ui/                       Primitives, Modal, Pagination, Coquille, Logo
│   └── lib/                      Téléchargement de blob
│
└── styles/globals.css            Jetons de la charte, thème clair et sombre
```

Les alias `@core/*`, `@features/*`, `@infra/*` et `@shared/*` rendent la couche
visible dans chaque import.

## Points de conception

**Un seul client HTTP.** `infrastructure/http/client.ts` est le seul module qui
connaisse l'URL de l'API, le format du jeton et la forme des erreurs. Une
réponse 401 y purge la session immédiatement, sans quoi toutes les requêtes
suivantes échoueraient de la même façon.

**La connexion mène à l'affectation, pas au tableau de bord.** C'est la
première tâche de la journée du superviseur : l'agent se présente, on note ses
itinéraires. Les chiffres viennent après.

**Le tableau ne clignote pas.** `placeholderData` garde la page précédente
affichée pendant le chargement de la suivante, et la recherche est différée de
350 ms — chaque frappe interrogerait sinon une table de plus de 400 000 lignes.

**La règle métier est rappelée, pas dupliquée.** Le formulaire de saisie
signale qu'un abonnement exige le numéro relevé, mais c'est l'API qui tranche.

**Le modal natif.** `<dialog>` apporte le piège de focus, la fermeture par
Échap et l'inertie de l'arrière-plan — trois choses qu'une modale maison rate
presque toujours.

## Charte graphique

Le bleu **`#1A76B9`** est échantillonné sur le logo. Les jetons sémantiques
(`--fond`, `--texte`, `--primaire`…) sont définis une fois dans
`styles/globals.css` et déclinés pour le thème sombre ; aucun composant
n'écrit une couleur en dur.

Les icônes d'application sont dérivées du logo par extraction de l'éclair du
« d'el », posé en blanc sur un carré bleu.

### Couleurs des graphiques

Palette validée pour la déficience de vision des couleurs et le contraste, sur
les deux surfaces réellement utilisées :

| Série | Clair (`#ffffff`) | Sombre (`#111a2b`) |
|---|---|---|
| Clients démarchés | `#1a76b9` | `#3b93dc` |
| Abonnements déclarés | `#eb6834` | `#d95926` |
| Abonnements confirmés | `#1baf7a` | `#199e70` |

Écart CVD minimal ΔE 9.2 en clair, 9.4 en sombre (seuil 8). L'aqua passe sous
3:1 sur fond blanc : l'identité des séries ne repose donc jamais sur la seule
couleur — légende permanente, étiquette directe en fin de courbe, et vue
tableau accessible sous le graphique.

## Commandes

```bash
pnpm install
pnpm dev          # http://localhost:3000
pnpm build
pnpm typecheck
pnpm lint
```

Le backend doit tourner sur le port 8000 ; l'URL est réglée par
`NEXT_PUBLIC_API_URL` dans `.env.local`.
