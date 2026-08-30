"""Politique de mot de passe.

Elle vit dans le domaine, et non dans un validateur de formulaire : la même
règle doit s'appliquer à l'inscription, au changement volontaire et à la
réinitialisation, quel que soit le chemin emprunté.

Le parti pris est celui des recommandations actuelles (NIST SP 800-63B) :
privilégier la **longueur** et refuser les mots de passe notoirement
compromis, plutôt qu'imposer un jeu de caractères qui pousse surtout à écrire
« Password1! » sur un papier collé à l'écran.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..errors import RegleMetierViolee

LONGUEUR_MIN = 10
LONGUEUR_MAX = 128

#: Mots de passe trop répandus pour être acceptés, quelle que soit leur forme.
#: Liste volontairement courte : la vraie défense est la longueur.
INTERDITS: frozenset[str] = frozenset(
    {
        "password", "motdepasse", "azerty", "qwerty", "123456", "1234567890",
        "socadel", "eneo", "cameroun", "nextltd", "bordereau", "whatsapp",
        "admin", "administrateur", "superviseur", "changeme", "iloveyou",
    }
)


@dataclass(frozen=True, slots=True)
class ForceMotDePasse:
    """Évaluation d'un mot de passe, telle qu'on l'affiche à la saisie."""

    score: int
    """De 0 (inacceptable) à 4 (excellent)."""

    acceptable: bool
    motifs: tuple[str, ...]
    """Ce qui manque, formulé pour être montré à l'utilisateur."""

    @property
    def libelle(self) -> str:
        return ("Très faible", "Faible", "Moyen", "Bon", "Excellent")[self.score]


def _normaliser(mot_de_passe: str) -> str:
    """Retire accents et casse, pour comparer au fond plutôt qu'à la forme.

    « Sôcadel » et « socadel » sont le même mot de passe du point de vue d'un
    attaquant qui déroule un dictionnaire.
    """
    sans_accent = "".join(
        c
        for c in unicodedata.normalize("NFD", mot_de_passe)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]", "", sans_accent.lower())


def evaluer(
    mot_de_passe: str, *, identifiant: str | None = None, email: str | None = None
) -> ForceMotDePasse:
    """Évalue un mot de passe sans le rejeter : sert au retour visuel.

    Args:
        mot_de_passe: la saisie à évaluer.
        identifiant: login du compte, pour interdire de le réutiliser.
        email: adresse du compte, même raison.
    """
    motifs: list[str] = []
    normalise = _normaliser(mot_de_passe)

    if len(mot_de_passe) < LONGUEUR_MIN:
        motifs.append(f"Au moins {LONGUEUR_MIN} caractères.")
    if len(mot_de_passe) > LONGUEUR_MAX:
        motifs.append(f"Au plus {LONGUEUR_MAX} caractères.")

    for interdit in INTERDITS:
        if interdit in normalise:
            motifs.append("Évitez les mots trop courants ou liés au projet.")
            break

    for valeur, quoi in ((identifiant, "identifiant"), (email, "adresse")):
        if valeur:
            racine = _normaliser(valeur.split("@")[0])
            if len(racine) >= 4 and racine in normalise:
                motifs.append(f"Ne reprenez pas votre {quoi}.")

    if re.fullmatch(r"(.)\1*", mot_de_passe or "x"):
        motifs.append("Un caractère répété ne protège rien.")

    # Le score récompense la longueur d'abord, la variété ensuite.
    familles = sum(
        bool(re.search(motif, mot_de_passe))
        for motif in (r"[a-z]", r"[A-Z]", r"\d", r"[^\w\s]")
    )
    score = 0
    if len(mot_de_passe) >= LONGUEUR_MIN:
        score = 1 + (len(mot_de_passe) >= 14) + (len(mot_de_passe) >= 18)
        score = min(score + (familles >= 3), 4)
    if motifs:
        score = min(score, 1)

    return ForceMotDePasse(
        score=score, acceptable=not motifs, motifs=tuple(dict.fromkeys(motifs))
    )


def exiger_valide(
    mot_de_passe: str,
    *,
    identifiant: str | None = None,
    email: str | None = None,
) -> None:
    """Garde appelée avant tout enregistrement de mot de passe.

    Raises:
        RegleMetierViolee: si la politique n'est pas respectée. Le message
            énumère ce qui manque, pour que l'utilisateur puisse corriger.
    """
    force = evaluer(mot_de_passe, identifiant=identifiant, email=email)
    if not force.acceptable:
        raise RegleMetierViolee(" ".join(force.motifs))


def exiger_confirmation(mot_de_passe: str, confirmation: str) -> None:
    """Vérifie la double saisie du formulaire d'inscription.

    Raises:
        RegleMetierViolee: si les deux saisies diffèrent.
    """
    if mot_de_passe != confirmation:
        raise RegleMetierViolee("Les deux mots de passe ne correspondent pas")
