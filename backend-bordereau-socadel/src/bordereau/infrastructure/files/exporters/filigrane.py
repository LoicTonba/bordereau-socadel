"""Filigrane du logo SOCADEL sur les documents exportés.

Il donne au document sa marque d'origine : une page imprimée circule seule,
détachée de l'application, et le filigrane atteste qu'elle en provient. Sur le
bordereau papier confié à l'agent, c'est aussi ce qui l'identifie comme un
document officiel de la campagne.

L'opacité est délibérément faible : le filigrane doit rester perceptible sans
jamais gêner la lecture des données ni l'écriture au stylo dans les cases.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from reportlab.lib.utils import ImageReader

#: Le logo est embarqué avec le paquet : le rendu ne doit dépendre d'aucun
#: fichier extérieur au déploiement.
CHEMIN_LOGO = Path(__file__).parent / "assets" / "logo-socadel.jpg"

#: Proportions du lockup source (1280 × 465).
RATIO_LOGO = 465 / 1280

OPACITE_FILIGRANE = 0.06
OPACITE_ENTETE = 1.0


@lru_cache(maxsize=1)
def _logo() -> ImageReader | None:
    """Charge le logo une seule fois pour tout le processus.

    Renvoie `None` si le fichier manque : un export sans filigrane vaut mieux
    qu'un export qui échoue.
    """
    if not CHEMIN_LOGO.exists():
        return None
    return ImageReader(str(CHEMIN_LOGO))


def dessiner_filigrane(canevas, largeur_page: float, hauteur_page: float) -> None:
    """Pose le logo en grand, centré et très pâle, sous le contenu.

    Appelée depuis le `onPage` de reportlab : le contenu est dessiné ensuite,
    donc par-dessus, et reste parfaitement lisible.
    """
    logo = _logo()
    if logo is None:
        return

    canevas.saveState()
    try:
        canevas.setFillAlpha(OPACITE_FILIGRANE)
        canevas.setStrokeAlpha(OPACITE_FILIGRANE)

        largeur = largeur_page * 0.72
        hauteur = largeur * RATIO_LOGO

        canevas.drawImage(
            logo,
            (largeur_page - largeur) / 2,
            (hauteur_page - hauteur) / 2,
            width=largeur,
            height=hauteur,
            mask="auto",
            preserveAspectRatio=True,
        )
    finally:
        # L'état est restauré quoi qu'il arrive : une alpha laissée à 0,06
        # rendrait tout le reste du document invisible.
        canevas.restoreState()


def dessiner_logo_entete(
    canevas, x: float, y: float, largeur: float
) -> float:
    """Pose le logo en pleine opacité dans l'en-tête du document.

    Returns:
        La hauteur occupée, pour que l'appelant place la suite en dessous.
    """
    logo = _logo()
    if logo is None:
        return 0.0

    hauteur = largeur * RATIO_LOGO
    canevas.saveState()
    try:
        canevas.setFillAlpha(OPACITE_ENTETE)
        canevas.drawImage(
            logo, x, y, width=largeur, height=hauteur,
            mask="auto", preserveAspectRatio=True,
        )
    finally:
        canevas.restoreState()

    return hauteur
