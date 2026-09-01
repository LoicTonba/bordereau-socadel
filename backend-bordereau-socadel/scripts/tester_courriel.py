"""Envoie un courriel de contrôle, pour vérifier la configuration du serveur.

    python scripts/tester_courriel.py destinataire@exemple.cm

Il passe par le même port `Messagerie` et le même gabarit que les messages du
cycle de vie d'un compte : si celui-ci arrive, les autres arriveront.

L'adaptateur choisi dépend de `.env`. Sans `SMTP_HOTE`, le message est déposé
dans `courriels/` et rien ne part sur Internet ; le script le dit, plutôt que
de laisser croire à un envoi.
"""

from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from bordereau.application.courriels.gabarit import (  # noqa: E402
    Bouton,
    Message,
    en_html,
    en_texte,
)
from bordereau.application.ports import Courriel  # noqa: E402
from bordereau.infrastructure.config.settings import get_settings  # noqa: E402
from bordereau.infrastructure.container import Container  # noqa: E402


def message_de_controle(destinataire: str, url: str) -> Courriel:
    contenu = Message(
        titre="Votre serveur d'envoi fonctionne",
        salutation="Bonjour",
        paragraphes=(
            "Ce message confirme que la plateforme Bordereau SOCADEL sait "
            "expédier ses courriels : confirmation d'adresse, ouverture "
            "d'accès, réinitialisation de mot de passe.",
            "Il est parti du même gabarit et du même serveur que les autres. "
            "Si vous le lisez, la chaîne est complète.",
        ),
        bouton=Bouton("Ouvrir la plateforme", url),
        reperes=(
            ("Destinataire", destinataire),
            ("Émis par", "scripts/tester_courriel.py"),
        ),
        paragraphes_finaux=(
            "Aucune action n'est attendue de votre part : ce message est un "
            "contrôle technique.",
        ),
    )
    return Courriel(
        destinataire=destinataire,
        sujet="Contrôle d'envoi, Bordereau SOCADEL",
        corps_texte=en_texte(contenu),
        corps_html=en_html(contenu),
    )


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage : python scripts/tester_courriel.py adresse@exemple.cm")

    reglages = get_settings()
    container = Container(reglages)

    if not reglages.smtp_hote:
        print(
            "Aucun serveur configure : le message va etre depose dans "
            f"{reglages.repertoire_courriels}, rien ne partira sur Internet."
        )
    else:
        print(
            f"Serveur : {reglages.smtp_hote}:{reglages.smtp_port}, "
            f"expediteur {reglages.expediteur_courriel}"
        )

    for destinataire in sys.argv[1:]:
        container.messagerie.envoyer(message_de_controle(destinataire, reglages.url_publique))
        print(f"  envoye a {destinataire}")

    print(
        "\nL'adaptateur avale ses erreurs par conception : un echec d'envoi ne "
        "doit jamais faire echouer une inscription. Regardez le journal "
        "ci-dessus si rien n'arrive."
    )


if __name__ == "__main__":
    main()
