"""Adaptateurs de sécurité : hachage bcrypt, jetons JWT, horloge système."""

from __future__ import annotations

from datetime import date, datetime, timezone

import bcrypt
import jwt

from ...application.errors import JetonInvalide
from ...application.ports import ContenuJeton
from ...domain.enums import Role


class HacheurBcrypt:
    """Implémente `HacheurMotDePasse` avec bcrypt.

    bcrypt tronque silencieusement au-delà de 72 octets : la troncature est
    faite explicitement pour que le comportement soit visible et stable.
    """

    LONGUEUR_MAX = 72

    def __init__(self, tours: int = 12) -> None:
        self._tours = tours

    def hacher(self, en_clair: str) -> str:
        octets = en_clair.encode("utf-8")[: self.LONGUEUR_MAX]
        return bcrypt.hashpw(octets, bcrypt.gensalt(self._tours)).decode("utf-8")

    def verifier(self, en_clair: str, empreinte: str) -> bool:
        try:
            return bcrypt.checkpw(
                en_clair.encode("utf-8")[: self.LONGUEUR_MAX],
                empreinte.encode("utf-8"),
            )
        except ValueError:
            # Empreinte corrompue ou d'un autre format : l'authentification
            # échoue, mais l'application ne tombe pas.
            return False


class ServiceJetonJwt:
    """Implémente `ServiceJeton` avec des JWT signés symétriquement."""

    def __init__(self, cle_secrete: str, algorithme: str = "HS256") -> None:
        self._cle = cle_secrete
        self._algorithme = algorithme

    def emettre(self, contenu: ContenuJeton) -> str:
        return jwt.encode(
            {
                "sub": str(contenu.utilisateur_id),
                "identifiant": contenu.identifiant,
                "role": contenu.role.value,
                "exp": int(contenu.expire_le.timestamp()),
            },
            self._cle,
            algorithm=self._algorithme,
        )

    def decoder(self, jeton: str) -> ContenuJeton:
        try:
            # L'expiration n'est pas tranchée ici mais par `RecupererSession`,
            # avec l'horloge injectée. Deux autorités sur le temps, celle de
            # PyJWT et celle du domaine, finissaient par diverger : un jeton
            # émis sous horloge figée était refusé dès que l'heure réelle
            # dépassait sa date de validité. La signature, elle, reste vérifiée.
            charge = jwt.decode(
                jeton,
                self._cle,
                algorithms=[self._algorithme],
                options={"verify_exp": False},
            )
        except jwt.PyJWTError as erreur:
            raise JetonInvalide("Jeton de session illisible") from erreur

        try:
            from uuid import UUID

            return ContenuJeton(
                utilisateur_id=UUID(charge["sub"]),
                identifiant=charge["identifiant"],
                role=Role(charge["role"]),
                expire_le=datetime.fromtimestamp(charge["exp"], tz=timezone.utc),
            )
        except (KeyError, ValueError) as erreur:
            raise JetonInvalide("Contenu du jeton inattendu") from erreur


class HorlogeSysteme:
    """Implémente `Horloge` sur l'heure de la machine, en UTC.

    Tout est daté en UTC en base ; l'affichage en heure locale (WAT, UTC+1)
    est du ressort du frontend.
    """

    def maintenant(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def aujourdhui(self) -> date:
        return self.maintenant().date()
