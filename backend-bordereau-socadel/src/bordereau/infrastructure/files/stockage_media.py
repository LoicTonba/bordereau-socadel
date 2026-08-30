"""Stockage des photos de profil.

Implémentation locale : les fichiers sont écrits sous un répertoire servi en
statique par l'API. C'est volontairement l'adaptateur le plus simple qui
fonctionne — le port `StockageMedia` permettra de basculer vers un stockage
objet le jour où plusieurs instances tourneront de front, sans toucher au reste.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol, runtime_checkable

#: Formats acceptés pour un portrait, avec leur extension canonique.
TYPES_ACCEPTES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

#: Une photo de profil n'a aucune raison d'être lourde : au-delà, c'est une
#: photo non redimensionnée, qui ralentira chaque affichage du répertoire.
TAILLE_MAX_OCTETS = 4 * 1024 * 1024


class MediaInvalide(Exception):
    """Le fichier déposé n'est pas une photo exploitable."""


@runtime_checkable
class StockageMedia(Protocol):
    """Port de stockage des fichiers média."""

    def enregistrer_photo(
        self, contenu: bytes, type_mime: str, *, prefixe: str
    ) -> str:
        """Écrit la photo et renvoie l'URL publique à stocker sur l'entité."""
        ...

    def supprimer(self, url: str) -> None: ...


class StockageMediaLocal:
    """Écrit les photos sur le disque local."""

    def __init__(self, racine: Path, prefixe_url: str = "/media") -> None:
        self._racine = racine
        self._prefixe_url = prefixe_url.rstrip("/")
        self._racine.mkdir(parents=True, exist_ok=True)

    def enregistrer_photo(
        self, contenu: bytes, type_mime: str, *, prefixe: str
    ) -> str:
        """Valide puis écrit la photo.

        Le nom de fichier dérive de l'empreinte du contenu : redéposer deux
        fois la même image ne crée pas deux fichiers, et le nom d'origine —
        qui vient du client, donc non fiable — n'est jamais réutilisé.

        Raises:
            MediaInvalide: type non accepté, fichier vide ou trop volumineux.
        """
        if not contenu:
            raise MediaInvalide("Le fichier déposé est vide")

        if len(contenu) > TAILLE_MAX_OCTETS:
            limite = TAILLE_MAX_OCTETS // (1024 * 1024)
            raise MediaInvalide(f"Photo trop volumineuse : limite {limite} Mo")

        extension = TYPES_ACCEPTES.get(type_mime.split(";")[0].strip().lower())
        if extension is None:
            formats = ", ".join(sorted(TYPES_ACCEPTES))
            raise MediaInvalide(f"Format non accepté. Attendu : {formats}")

        if not self._est_une_image(contenu, extension):
            # Le type MIME est déclaré par le client : on vérifie la signature
            # réelle du fichier plutôt que de le croire sur parole.
            raise MediaInvalide(
                "Le contenu du fichier ne correspond pas à une image"
            )

        empreinte = hashlib.sha256(contenu).hexdigest()[:24]
        nom = f"{_assainir(prefixe)}-{empreinte}{extension}"
        (self._racine / nom).write_bytes(contenu)

        return f"{self._prefixe_url}/{nom}"

    def supprimer(self, url: str) -> None:
        nom = Path(url).name
        chemin = self._racine / nom
        # `resolve` empêche qu'une URL forgée avec des `..` sorte du dépôt.
        if chemin.resolve().parent == self._racine.resolve() and chemin.exists():
            chemin.unlink()

    @staticmethod
    def _est_une_image(contenu: bytes, extension: str) -> bool:
        """Contrôle la signature binaire (magic number) du fichier."""
        signatures = {
            ".jpg": (b"\xff\xd8\xff",),
            ".png": (b"\x89PNG\r\n\x1a\n",),
            ".webp": (b"RIFF",),
        }
        return any(contenu.startswith(s) for s in signatures.get(extension, ()))


def _assainir(valeur: str) -> str:
    """Ne garde que ce qui peut figurer sans risque dans un nom de fichier."""
    propre = "".join(c if c.isalnum() or c in "-_" else "-" for c in valeur.lower())
    return propre.strip("-")[:40] or "media"
