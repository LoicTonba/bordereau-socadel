"""Rend les cinq courriels dans un fichier unique, pour les relire d'un bloc.

    python scripts/apercu_courriels.py [sortie.html]

Aucune base ni serveur : les comptes sont fabriqués en mémoire. Le fichier
produit sert à valider la mise en page avant de l'envoyer à qui que ce soit.
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from bordereau.application import courriels  # noqa: E402
from bordereau.domain.entities import Utilisateur  # noqa: E402
from bordereau.domain.enums import Role, StatutCompte  # noqa: E402

SORTIE = RACINE.parent / "Documents" / "Courriels-Bordereau-SOCADEL.html"

URL = "https://bordereau.socadel.cm"
JETON = "N3xT-LtD-jeton-de-demonstration-uniquement"


def _compte(role: Role, agence: str | None = None) -> Utilisateur:
    return Utilisateur(
        id=uuid4(),
        identifiant="mbarga.j",
        nom_complet="MBARGA Jeanne",
        email="jeanne.mbarga@socadel.cm",
        empreinte_mot_de_passe="x",
        role=role,
        statut=StatutCompte.ACTIF,
        agence=agence,
    )


def main() -> None:
    sortie = Path(sys.argv[1]) if len(sys.argv) > 1 else SORTIE

    superviseur = _compte(Role.SUPERVISEUR, "CSC_ESSOS")
    exemples = [
        (
            "1. Confirmation d'adresse, à l'inscription",
            courriels.verification_adresse(
                superviseur, f"{URL}/verification?jeton={JETON}"
            ),
        ),
        (
            "2. Accès ouvert, après approbation par un responsable",
            courriels.acces_ouvert(superviseur, f"{URL}/login"),
        ),
        (
            "3. Demande refusée",
            courriels.demande_refusee(
                superviseur, "Aucun poste de superviseur ouvert à Essos ce trimestre."
            ),
        ),
        (
            "4. Mot de passe oublié, lien de réinitialisation",
            courriels.reinitialisation_demandee(
                superviseur, f"{URL}/reinitialisation?jeton={JETON}"
            ),
        ),
        (
            "5. Mot de passe réinitialisé par un responsable",
            courriels.reinitialisation_par_responsable(superviseur),
        ),
    ]

    blocs = []
    for titre, courriel in exemples:
        blocs.append(
            f"""<section>
  <h2>{titre}</h2>
  <p class="sujet"><strong>Sujet</strong> : {courriel.sujet}</p>
  <iframe srcdoc="{_echapper(courriel.corps_html or '')}" loading="lazy"></iframe>
  <details>
    <summary>Version texte, ce que lit un client sans HTML</summary>
    <pre>{courriel.corps_texte}</pre>
  </details>
</section>"""
        )

    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(_page("\n".join(blocs)), encoding="utf-8")
    print(f"Apercu genere : {sortie}  ({sortie.stat().st_size / 1024:.0f} Ko)")


def _echapper(html: str) -> str:
    """Le HTML entre dans un attribut `srcdoc` : seuls les guillemets gênent."""
    return html.replace("&", "&amp;").replace('"', "&quot;")


def _page(contenu: str) -> str:
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Courriels, Bordereau SOCADEL</title>
<style>
  body {{ margin:0; padding:32px 20px 60px; background:#eef2f7;
         font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
         color:#0f172a; }}
  h1 {{ max-width:640px; margin:0 auto 6px; font-size:22px; }}
  .chapeau {{ max-width:640px; margin:0 auto 34px; font-size:14px; color:#475569;
              line-height:1.6; }}
  section {{ max-width:640px; margin:0 auto 40px; }}
  h2 {{ font-size:14px; font-weight:600; color:#1f5fa0; margin:0 0 6px;
        text-transform:uppercase; letter-spacing:0.4px; }}
  .sujet {{ margin:0 0 12px; font-size:13px; color:#475569; }}
  iframe {{ width:100%; height:700px; border:1px solid #cbd5e1; border-radius:12px;
            background:#fff; }}
  details {{ margin-top:10px; font-size:13px; color:#475569; }}
  summary {{ cursor:pointer; }}
  pre {{ background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:16px;
         white-space:pre-wrap; font-size:12.5px; line-height:1.6; }}
</style>
</head>
<body>
<h1>Les courriels du cycle de vie d'un compte</h1>
<p class="chapeau">
  Cinq messages, un seul gabarit. Chacun part en deux versions : la mise en page
  ci-dessous, et une version texte que l'on peut déplier sous chaque exemple,
  pour les clients qui refusent le HTML. Les liens sont fictifs.
</p>
{contenu}
</body>
</html>
"""


if __name__ == "__main__":
    main()
