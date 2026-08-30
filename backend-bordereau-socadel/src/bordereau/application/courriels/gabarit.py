"""Gabarit HTML des courriels transactionnels.

Pourquoi ici et pas dans l'infrastructure : ce module ne parle ni de SMTP ni de
fichier, il met en forme **ce que nous disons**. Le transport, lui, reste
derrière le port `Messagerie` et peut changer sans toucher à une ligne d'ici.

Trois contraintes dictent la mise en page, et expliquent un balisage qui
paraîtrait daté sur le Web :

* les clients de messagerie ignorent les feuilles de style externes et une
  bonne partie de la mise en page moderne, d'où des tableaux imbriqués et des
  styles en ligne ;
* les images distantes sont bloquées par défaut, d'où un logo composé en
  texte plutôt qu'un fichier joint ou une URL ;
* le mode sombre recolorie ce qu'il ne comprend pas, d'où des fonds toujours
  déclarés explicitement.

Chaque message part en deux versions, texte et HTML. Le texte n'est pas un
repli négligé : c'est ce que lisent les clients en mode dégradé et les lecteurs
d'écran mal configurés.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

# --- Charte -----------------------------------------------------------------

BLEU = "#1a76b9"
BLEU_SOMBRE = "#1f5fa0"
BLEU_TRES_CLAIR = "#eff7fd"
BLANC = "#ffffff"
FOND = "#f6f8fb"
TEXTE = "#0f172a"
TEXTE_DOUX = "#475569"
TEXTE_TRES_DOUX = "#64748b"
BORDURE = "#e2e8f0"
AMBRE = "#b45309"
AMBRE_FOND = "#fffbeb"

POLICE = (
    "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
)

LARGEUR = 600

PIED_LIGNES = (
    "Bordereau SOCADEL, plateforme de collecte des numéros WhatsApp.",
    "Une solution NEXT LTD, Numeric Export Technologies.",
    "Ce message est automatique, merci de ne pas y répondre.",
)


@dataclass(frozen=True, slots=True)
class Bouton:
    """L'action unique du message. Un courriel qui en propose deux n'en fait
    faire aucune."""

    libelle: str
    lien: str


@dataclass(frozen=True, slots=True)
class Message:
    """Le contenu d'un courriel, indépendamment de sa mise en forme."""

    titre: str
    salutation: str
    paragraphes: tuple[str, ...]
    bouton: Bouton | None = None
    #: Couples libellé/valeur affichés en tableau, par exemple le périmètre.
    reperes: tuple[tuple[str, str], ...] = ()
    #: Mention de sécurité, encadrée en bas du message.
    avertissement: str | None = None
    #: Texte gris sous le bouton, typiquement la durée de validité du lien.
    mention_lien: str | None = None
    paragraphes_finaux: tuple[str, ...] = field(default=())


# --- Rendu texte ------------------------------------------------------------


def en_texte(message: Message) -> str:
    """Version texte, lisible telle quelle dans un terminal ou un client sobre."""
    morceaux: list[str] = [f"{message.salutation},", ""]
    morceaux.extend(_paragraphes_texte(message.paragraphes))

    if message.reperes:
        largeur = max(len(libelle) for libelle, _ in message.reperes)
        for libelle, valeur in message.reperes:
            morceaux.append(f"  {libelle.ljust(largeur)} : {valeur}")
        morceaux.append("")

    if message.bouton:
        morceaux.append(message.bouton.libelle + " :")
        morceaux.append(message.bouton.lien)
        morceaux.append("")

    if message.mention_lien:
        morceaux.extend([message.mention_lien, ""])

    morceaux.extend(_paragraphes_texte(message.paragraphes_finaux))

    if message.avertissement:
        morceaux.extend([message.avertissement, ""])

    morceaux.append("-" * 60)
    morceaux.extend(PIED_LIGNES)
    return "\n".join(morceaux).rstrip() + "\n"


def _paragraphes_texte(paragraphes: tuple[str, ...]) -> list[str]:
    lignes: list[str] = []
    for paragraphe in paragraphes:
        lignes.extend([paragraphe, ""])
    return lignes


# --- Rendu HTML -------------------------------------------------------------


def en_html(message: Message) -> str:
    """Version HTML, mise en page pour les clients de messagerie."""
    corps = [
        _titre(message.titre),
        _paragraphe(f"{escape(message.salutation)},"),
        *[_paragraphe(escape(p)) for p in message.paragraphes],
    ]

    if message.reperes:
        corps.append(_reperes(message.reperes))
    if message.bouton:
        corps.append(_bouton(message.bouton))
    if message.mention_lien:
        corps.append(_mention_lien(message.mention_lien, message.bouton))
    corps.extend(_paragraphe(escape(p)) for p in message.paragraphes_finaux)
    if message.avertissement:
        corps.append(_avertissement(message.avertissement))

    return _document("".join(corps), apercu=message.paragraphes[0] if message.paragraphes else "")


def _document(contenu: str, *, apercu: str) -> str:
    """Enveloppe complète : préheader, bandeau, carte, pied."""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>Bordereau SOCADEL</title>
</head>
<body style="margin:0;padding:0;background:{FOND};">
<!-- Aperçu affiché dans la liste des messages, avant même l'ouverture. -->
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(apercu)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{FOND};padding:32px 16px;">
  <tr>
    <td align="center">
      <table role="presentation" width="{LARGEUR}" cellpadding="0" cellspacing="0" border="0"
             style="width:100%;max-width:{LARGEUR}px;">
        {_bandeau()}
        <tr>
          <td style="background:{BLANC};border:1px solid {BORDURE};border-top:0;
                     border-radius:0 0 14px 14px;padding:32px 34px 34px;">
            {contenu}
          </td>
        </tr>
        {_pied()}
      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""


def _bandeau() -> str:
    """Le bandeau porte la marque en texte : une image serait bloquée."""
    return f"""<tr>
          <td style="background:{BLEU};border-radius:14px 14px 0 0;padding:26px 34px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="font-family:{POLICE};font-size:23px;line-height:1;
                           font-weight:700;color:{BLANC};letter-spacing:-0.4px;">
                  socad<span style="color:#bfe0f7;">&rsquo;</span>el
                </td>
              </tr>
              <tr>
                <td style="padding-top:6px;font-family:{POLICE};font-size:11px;
                           line-height:1.4;color:#bfe0f7;letter-spacing:0.3px;">
                  Société Camerounaise d&rsquo;Electricité
                </td>
              </tr>
            </table>
          </td>
        </tr>"""


def _pied() -> str:
    lignes = "<br>".join(escape(ligne) for ligne in PIED_LIGNES)
    return f"""<tr>
          <td style="padding:22px 34px 0;font-family:{POLICE};font-size:11px;
                     line-height:1.7;color:{TEXTE_TRES_DOUX};text-align:center;">
            {lignes}
          </td>
        </tr>"""


def _titre(texte: str) -> str:
    return (
        f'<h1 style="margin:0 0 18px;font-family:{POLICE};font-size:20px;'
        f'line-height:1.35;font-weight:600;color:{TEXTE};">{escape(texte)}</h1>'
    )


def _paragraphe(html: str) -> str:
    return (
        f'<p style="margin:0 0 14px;font-family:{POLICE};font-size:15px;'
        f'line-height:1.65;color:{TEXTE_DOUX};">{html}</p>'
    )


def _reperes(reperes: tuple[tuple[str, str], ...]) -> str:
    """Les repères du compte, en deux colonnes.

    Le remplissage est porté par les cellules et non par le tableau : Outlook
    ignore un `padding` posé sur un `<table>`, et le bloc se retrouverait collé
    à ses bords.
    """
    lignes = "".join(
        f"""<tr>
              <td style="padding:7px 0;font-family:{POLICE};font-size:13px;
                         color:{TEXTE_TRES_DOUX};white-space:nowrap;">{escape(libelle)}</td>
              <td style="padding:7px 0 7px 22px;font-family:{POLICE};font-size:14px;
                         font-weight:600;color:{TEXTE};">{escape(valeur)}</td>
            </tr>"""
        for libelle, valeur in reperes
    )
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="margin:4px 0 24px;background:{BLEU_TRES_CLAIR};border-radius:10px;">
  <tr>
    <td style="padding:12px 20px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        {lignes}
      </table>
    </td>
  </tr>
</table>"""


def _bouton(bouton: Bouton) -> str:
    """Bouton en tableau : Outlook n'arrondit pas un lien stylé en bloc."""
    lien = escape(bouton.lien, quote=True)
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 4px;">
  <tr>
    <td style="background:{BLEU};border-radius:9px;">
      <a href="{lien}"
         style="display:inline-block;padding:13px 26px;font-family:{POLICE};font-size:15px;
                font-weight:600;color:{BLANC};text-decoration:none;border-radius:9px;">
        {escape(bouton.libelle)}
      </a>
    </td>
  </tr>
</table>"""


def _mention_lien(mention: str, bouton: Bouton | None) -> str:
    """La mention rappelle la durée de validité et donne le lien en clair.

    Le lien brut n'est pas une redondance : certains clients neutralisent les
    boutons, et un destinataire méfiant préfère lire l'adresse avant de cliquer.
    """
    brut = (
        f'<br><span style="color:{TEXTE_TRES_DOUX};word-break:break-all;">'
        f"{escape(bouton.lien)}</span>"
        if bouton
        else ""
    )
    return (
        f'<p style="margin:10px 0 18px;font-family:{POLICE};font-size:12.5px;'
        f'line-height:1.65;color:{TEXTE_DOUX};">{escape(mention)}{brut}</p>'
    )


def _avertissement(texte: str) -> str:
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="margin-top:8px;background:{AMBRE_FOND};border-left:3px solid {AMBRE};border-radius:0 8px 8px 0;">
  <tr>
    <td style="padding:13px 16px;font-family:{POLICE};font-size:13px;line-height:1.6;color:{AMBRE};">
      {escape(texte)}
    </td>
  </tr>
</table>"""
