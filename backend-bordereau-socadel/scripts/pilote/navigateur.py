"""Pilote de navigateur minimal, en CDP direct.

Il n'y a ni Playwright ni Puppeteer sur ce poste, et en installer un pour
prendre des captures serait disproportionné. Chrome expose déjà tout ce qu'il
faut par son protocole de débogage : on le lance avec un port ouvert, on parle
WebSocket, et on obtient la navigation, la saisie et la capture.

Deux points méritent un mot.

Les champs React sont **contrôlés** : écrire dans `value` ne suffit pas, le
composant réécrirait l'ancienne valeur au rendu suivant. Il faut passer par le
mutateur natif puis émettre l'évènement `input`, ce que fait `remplir`.

Les attentes sont **explicites**, jamais des pauses fixes : on attend qu'un
sélecteur apparaisse, ce qui reste vrai que la machine soit lente ou rapide.
"""

from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

import websockets

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

#: Au-delà, on considère que la page ne viendra pas.
DELAI_MAX = 25.0

#: Intervalle entre deux vérifications d'un sélecteur, en secondes.
PAS = 0.15


class EchecPilote(RuntimeError):
    """Le navigateur n'a pas fait ce qu'on lui demandait."""


@dataclass(slots=True)
class Navigateur:
    """Une session Chrome et l'onglet unique qu'elle pilote."""

    processus: subprocess.Popen
    profil: tempfile.TemporaryDirectory
    connexion: object
    _compteur: int = 0

    async def _appel(self, methode: str, **parametres):
        self._compteur += 1
        identifiant = self._compteur
        await self.connexion.send(
            json.dumps({"id": identifiant, "method": methode, "params": parametres})
        )
        while True:
            message = json.loads(await self.connexion.recv())
            if message.get("id") != identifiant:
                continue  # Évènement de page, sans intérêt ici.
            if "error" in message:
                raise EchecPilote(f"{methode} : {message['error']}")
            return message.get("result", {})

    async def evaluer(self, expression: str):
        """Évalue du JavaScript dans la page et renvoie sa valeur."""
        resultat = await self._appel(
            "Runtime.evaluate",
            expression=expression,
            returnByValue=True,
            awaitPromise=True,
        )
        if resultat.get("exceptionDetails"):
            details = resultat["exceptionDetails"]
            raise EchecPilote(details.get("text", "erreur JavaScript"))
        return resultat.get("result", {}).get("value")

    async def aller(self, url: str) -> None:
        await self._appel("Page.navigate", url=url)
        await self.attendre("body")

    async def attendre(self, selecteur: str, *, texte: str | None = None) -> None:
        """Attend qu'un élément existe, éventuellement porteur d'un texte.

        Le texte sert quand le sélecteur seul ne distingue pas les états : la
        même carte est présente avant et après le chargement des données.
        """
        expression = _expression_presence(selecteur, texte)
        ecoule = 0.0
        while ecoule < DELAI_MAX:
            if await self.evaluer(expression):
                # Un battement de plus laisse React peindre ce qu'il vient de
                # monter, faute de quoi la capture attrape un écran à moitié
                # dessiné.
                await asyncio.sleep(0.35)
                return
            await asyncio.sleep(PAS)
            ecoule += PAS
        raise EchecPilote(f"introuvable après {DELAI_MAX:.0f} s : {selecteur} {texte or ''}")

    async def attendre_texte(self, *textes: str) -> str:
        """Attend qu'un des textes apparaisse dans la page, et dit lequel.

        Utile quand une action a deux issues attendues : l'affectation rend
        une carte de succes ou une alerte de refus, et le pilote doit
        poursuivre dans les deux cas.
        """
        ecoule = 0.0
        while ecoule < DELAI_MAX:
            corps = await self.evaluer("document.body.innerText")
            for texte in textes:
                if texte in (corps or ""):
                    await asyncio.sleep(0.35)
                    return texte
            await asyncio.sleep(PAS)
            ecoule += PAS
        raise EchecPilote(f"aucun de ces textes apres {DELAI_MAX:.0f} s : {textes}")

    async def cliquer(self, selecteur: str, *, texte: str | None = None) -> None:
        """Clique le premier élément correspondant."""
        await self.attendre(selecteur, texte=texte)
        clique = await self.evaluer(
            f"(() => {{ const e = {_expression_element(selecteur, texte)};"
            f" if (!e) return false; e.click(); return true; }})()"
        )
        if not clique:
            raise EchecPilote(f"clic impossible : {selecteur} {texte or ''}")
        await asyncio.sleep(0.3)

    async def cliquer_dans_ligne(self, reperage: str, libelle: str) -> None:
        """Clique un bouton situé dans la ligne de tableau qui porte un repère.

        Les tableaux du bordereau n'ont pas d'identifiant par ligne : le
        contrat du client sert de repère, il est unique et visible à l'écran.
        """
        await self.attendre("tbody tr", texte=reperage)
        clique = await self.evaluer(
            "(() => { const l = [...document.querySelectorAll('tbody tr')]"
            f"   .find(l => l.innerText.includes({json.dumps(reperage)}));"
            " if (!l) return false;"
            " const b = [...l.querySelectorAll('button')]"
            f"   .find(b => b.innerText.includes({json.dumps(libelle)}));"
            " if (!b) return false; b.click(); return true; })()"
        )
        if not clique:
            raise EchecPilote(f"bouton « {libelle} » absent de la ligne {reperage}")
        await asyncio.sleep(0.4)

    async def remplir(self, selecteur: str, valeur: str) -> None:
        """Renseigne un champ contrôlé par React."""
        await self.attendre(selecteur)
        ecrit = await self.evaluer(
            "(() => {"
            f" const e = document.querySelector({json.dumps(selecteur)});"
            " if (!e) return false;"
            " const proto = e instanceof HTMLTextAreaElement"
            "   ? window.HTMLTextAreaElement.prototype"
            "   : window.HTMLInputElement.prototype;"
            " const mutateur = Object.getOwnPropertyDescriptor(proto, 'value').set;"
            f" mutateur.call(e, {json.dumps(valeur)});"
            " e.dispatchEvent(new Event('input', {bubbles: true}));"
            " return true; })()"
        )
        if not ecrit:
            raise EchecPilote(f"champ introuvable : {selecteur}")
        await asyncio.sleep(0.2)

    async def assainir(self) -> None:
        """Retire de la page ce qui ne doit pas figurer dans un guide.

        Le badge de développement de Next.js flotte au-dessus de l'interface :
        il n'existe qu'en développement et n'apprendrait rien au lecteur.
        """
        await self.evaluer(
            "(() => { let s = document.getElementById('capture-assainie');"
            " if (!s) { s = document.createElement('style');"
            " s.id = 'capture-assainie'; document.head.appendChild(s); }"
            " s.textContent = 'nextjs-portal, [data-nextjs-toast],"
            " #__next-build-watcher { display: none !important; }';"
            " return true; })()"
        )

    async def capturer(self, chemin: Path, *, pleine_page: bool = False) -> Path:
        """Enregistre une capture PNG."""
        await self.assainir()
        parametres = {"format": "png"}
        if pleine_page:
            parametres["captureBeyondViewport"] = True
        resultat = await self._appel("Page.captureScreenshot", **parametres)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(base64.b64decode(resultat["data"]))
        return chemin

    async def fermer(self) -> None:
        try:
            await self.connexion.close()
        finally:
            self.processus.terminate()
            try:
                self.processus.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.processus.kill()
            self.profil.cleanup()


def _expression_element(selecteur: str, texte: str | None) -> str:
    cible = json.dumps(selecteur)
    if texte is None:
        return f"document.querySelector({cible})"
    return (
        f"[...document.querySelectorAll({cible})].find("
        f"n => (n.innerText || '').includes({json.dumps(texte)}))"
    )


def _expression_presence(selecteur: str, texte: str | None) -> str:
    return f"Boolean({_expression_element(selecteur, texte)})"


async def ouvrir(largeur: int = 1440, hauteur: int = 900) -> Navigateur:
    """Lance Chrome et se branche sur son onglet."""
    if not CHROME.exists():
        raise EchecPilote(f"Chrome introuvable : {CHROME}")

    profil = tempfile.TemporaryDirectory(prefix="socadel-captures-")
    processus = subprocess.Popen(
        [
            str(CHROME),
            "--headless=new",
            "--remote-debugging-port=9333",
            f"--user-data-dir={profil.name}",
            f"--window-size={largeur},{hauteur}",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",  # Captures nettes à l'impression.
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url_debogage = await _attendre_debogage()
    connexion = await websockets.connect(url_debogage, max_size=64 * 1024 * 1024)
    navigateur = Navigateur(processus, profil, connexion)
    await navigateur._appel("Page.enable")
    await navigateur._appel("Runtime.enable")
    # Le thème clair est imposé : les captures d'un guide doivent être
    # homogènes, et Chrome sans interface suit le thème sombre du système.
    await navigateur._appel(
        "Emulation.setEmulatedMedia",
        features=[{"name": "prefers-color-scheme", "value": "light"}],
    )
    return navigateur


async def _attendre_debogage() -> str:
    """Attend que Chrome publie l'adresse WebSocket de son onglet."""
    ecoule = 0.0
    while ecoule < DELAI_MAX:
        try:
            with urlopen("http://127.0.0.1:9333/json/list", timeout=2) as reponse:
                cibles = json.load(reponse)
            for cible in cibles:
                if cible.get("type") == "page":
                    return cible["webSocketDebuggerUrl"]
        except OSError:
            pass
        await asyncio.sleep(0.3)
        ecoule += 0.3
    raise EchecPilote("Chrome n'a pas ouvert son port de débogage")
