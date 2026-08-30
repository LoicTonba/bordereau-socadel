"""Objet-valeur : numéro de téléphone camerounais au format E.164."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..errors import ValidationError

INDICATIF_CAMEROUN = "237"

#: Préfixes camerounais valides après l'indicatif (6 = mobile, 2 = fixe).
_E164_CM = re.compile(r"^\+237[62]\d{8}$")
_NON_CHIFFRE = re.compile(r"[^0-9+]")


@dataclass(frozen=True, slots=True)
class NumeroTelephone:
    """Numéro normalisé `+237XXXXXXXXX`.

    Les fichiers sources contiennent des saisies hétérogènes (`694174768`,
    `237694174768`, `+237 694 17 47 68`...) : `parse` les ramène toutes à la
    forme canonique E.164, seule forme stockée en base et seule forme
    comparable avec la source de vérité WhatsApp.
    """

    valeur: str

    def __post_init__(self) -> None:
        if not _E164_CM.match(self.valeur):
            raise ValidationError(
                f"Numéro de téléphone camerounais invalide : {self.valeur!r}"
            )

    @classmethod
    def parse(cls, brut: str | int | None) -> "NumeroTelephone":
        """Normalise une saisie libre en numéro E.164.

        Raises:
            ValidationError: si la saisie ne peut pas être ramenée à un
                numéro camerounais valide.
        """
        if brut is None:
            raise ValidationError("Numéro de téléphone manquant")

        nettoye = _NON_CHIFFRE.sub("", str(brut))
        if not nettoye:
            raise ValidationError("Numéro de téléphone vide après normalisation")

        chiffres = nettoye.lstrip("+")
        if chiffres.startswith("00"):
            chiffres = chiffres[2:]
        if not chiffres.startswith(INDICATIF_CAMEROUN):
            chiffres = INDICATIF_CAMEROUN + chiffres

        return cls(f"+{chiffres}")

    @classmethod
    def parse_ou_none(cls, brut: str | int | None) -> "NumeroTelephone | None":
        """Variante tolérante : un import de 400 000 lignes ne doit pas échouer
        en bloc à cause d'une saisie isolée."""
        try:
            return cls.parse(brut)
        except ValidationError:
            return None

    @property
    def national(self) -> str:
        """Numéro sans indicatif, tel qu'affiché sur le terrain."""
        return self.valeur[len(INDICATIF_CAMEROUN) + 1 :]

    @property
    def est_mobile(self) -> bool:
        return self.national.startswith("6")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.valeur
