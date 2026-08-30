"""Adaptateurs de messagerie et de jetons.

Deux implémentations du port `Messagerie` :

* `MessagerieFichier` écrit chaque message dans un répertoire. C'est
  l'adaptateur de développement : on relit le courriel et on suit le lien sans
  dépendre d'un serveur de messagerie.
* `MessagerieSmtp` parle à un vrai serveur.

Toutes deux **avalent leurs erreurs**. Un compte créé dont le courriel n'est
pas parti reste un compte créé : faire échouer l'inscription parce que le
serveur SMTP tousse serait pire que ne pas envoyer le message, qui peut de
toute façon être renvoyé.
"""

from __future__ import annotations

import logging
import secrets
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from ...application.ports import Courriel

logger = logging.getLogger(__name__)

#: Longueur du jeton en octets avant encodage. 32 octets donnent 43 caractères
#: URL-safe, hors de portée d'une énumération.
OCTETS_JETON = 32


class GenerateurJetonAleatoire:
    """Implémente `GenerateurJeton` avec le générateur cryptographique."""

    def nouveau(self) -> str:
        return secrets.token_urlsafe(OCTETS_JETON)


class MessagerieFichier:
    """Écrit les courriels sur disque, un fichier par message.

    Le lien de confirmation reste ainsi consultable en développement, sans
    configurer quoi que ce soit.
    """

    def __init__(self, repertoire: Path) -> None:
        self._repertoire = repertoire
        self._repertoire.mkdir(parents=True, exist_ok=True)

    def envoyer(self, courriel: Courriel) -> None:
        horodatage = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        destinataire = "".join(
            c if c.isalnum() else "-" for c in courriel.destinataire
        )[:40]
        chemin = self._repertoire / f"{horodatage}-{destinataire}.txt"

        try:
            chemin.write_text(
                f"À      : {courriel.destinataire}\n"
                f"Sujet  : {courriel.sujet}\n"
                f"{'-' * 70}\n\n{courriel.corps_texte}\n",
                encoding="utf-8",
            )
            logger.info("Courriel écrit dans %s", chemin)
        except OSError:
            logger.exception("Impossible d'écrire le courriel pour %s",
                             courriel.destinataire)


class MessagerieSmtp:
    """Envoie par un serveur SMTP."""

    def __init__(
        self,
        hote: str,
        port: int,
        expediteur: str,
        *,
        utilisateur: str | None = None,
        mot_de_passe: str | None = None,
        tls: bool = True,
        delai: float = 10.0,
    ) -> None:
        self._hote = hote
        self._port = port
        self._expediteur = expediteur
        self._utilisateur = utilisateur
        self._mot_de_passe = mot_de_passe
        self._tls = tls
        self._delai = delai

    def envoyer(self, courriel: Courriel) -> None:
        message = EmailMessage()
        message["From"] = self._expediteur
        message["To"] = courriel.destinataire
        message["Subject"] = courriel.sujet
        message.set_content(courriel.corps_texte)
        if courriel.corps_html:
            message.add_alternative(courriel.corps_html, subtype="html")

        try:
            with smtplib.SMTP(self._hote, self._port, timeout=self._delai) as serveur:
                if self._tls:
                    serveur.starttls()
                if self._utilisateur and self._mot_de_passe:
                    serveur.login(self._utilisateur, self._mot_de_passe)
                serveur.send_message(message)
            logger.info("Courriel envoyé à %s", courriel.destinataire)
        except (smtplib.SMTPException, OSError):
            # L'échec est tracé, jamais propagé : voir l'en-tête du module.
            logger.exception(
                "Envoi du courriel impossible vers %s", courriel.destinataire
            )
