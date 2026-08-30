"""Les cinq courriels du cycle de vie d'un compte.

Ils sont rassemblés ici plutôt que dispersés dans les cas d'usage : c'est ce
qu'un compte reçoit, et cela se relit d'un bloc. Chacun rend une version texte
et une version HTML à partir du même contenu, ce qui évite les deux versions
qui divergent avec le temps.

Le ton suit la même règle partout : dire ce qui vient d'arriver, dire quoi
faire, dire quoi faire si l'on n'y est pour rien.
"""

from __future__ import annotations

from ...domain.entities import Utilisateur
from ..ports import Courriel
from .gabarit import Bouton, Message, en_html, en_texte

#: Libellés de rôle destinés au lecteur, pas au code.
LIBELLE_ROLE = {
    "SUPER_UTILISATEUR": "Super utilisateur",
    "ADMINISTRATEUR": "Administrateur",
    "SUPERVISEUR": "Superviseur",
    "AGENT_TERRAIN": "Agent de terrain",
}


def _rendre(compte: Utilisateur, sujet: str, message: Message) -> Courriel:
    return Courriel(
        destinataire=compte.email,
        sujet=sujet,
        corps_texte=en_texte(message),
        corps_html=en_html(message),
    )


def verification_adresse(compte: Utilisateur, lien: str) -> Courriel:
    """Premier message : prouver que l'adresse existe et appartient au demandeur."""
    return _rendre(
        compte,
        "Confirmez votre adresse, Bordereau SOCADEL",
        Message(
            titre="Confirmez votre adresse",
            salutation=f"Bonjour {compte.nom_complet}",
            paragraphes=(
                "Une demande d'accès à la plateforme Bordereau SOCADEL a été "
                f"déposée avec cette adresse, sous l'identifiant « {compte.identifiant} ».",
                "Confirmez qu'elle est bien la vôtre pour que votre demande "
                "puisse être examinée.",
            ),
            bouton=Bouton("Confirmer mon adresse", lien),
            mention_lien=(
                "Ce lien est valable trois jours. Si le bouton ne fonctionne "
                "pas, copiez cette adresse dans votre navigateur :"
            ),
            paragraphes_finaux=(
                "Une fois l'adresse confirmée, un responsable examinera votre "
                "demande et vous attribuera vos droits. Vous recevrez alors un "
                "second message.",
            ),
            avertissement=(
                "Si vous n'êtes pas à l'origine de cette demande, ignorez ce "
                "message : aucun accès ne sera ouvert."
            ),
        ),
    )


def acces_ouvert(compte: Utilisateur, lien: str) -> Courriel:
    """Deuxième message : un responsable a approuvé, le compte est utilisable."""
    perimetre = compte.agence or compte.region or "Portée nationale"
    return _rendre(
        compte,
        "Votre accès est ouvert, Bordereau SOCADEL",
        Message(
            titre="Votre accès est ouvert",
            salutation=f"Bonjour {compte.nom_complet}",
            paragraphes=("Votre demande d'accès a été approuvée.",),
            reperes=(
                ("Identifiant", compte.identifiant),
                ("Profil", LIBELLE_ROLE.get(compte.role.value, compte.role.value)),
                ("Périmètre", perimetre),
            ),
            bouton=Bouton("Me connecter", lien),
            paragraphes_finaux=(
                "Connectez-vous avec le mot de passe que vous avez choisi lors "
                "de votre inscription. À la connexion, indiquez votre profil "
                "puis l'agence où vous vous trouvez.",
            ),
        ),
    )


def demande_refusee(compte: Utilisateur, motif: str | None) -> Courriel:
    """Troisième message : la demande n'a pas été retenue."""
    return _rendre(
        compte,
        "Votre demande d'accès, Bordereau SOCADEL",
        Message(
            titre="Votre demande d'accès",
            salutation=f"Bonjour {compte.nom_complet}",
            paragraphes=("Votre demande d'accès n'a pas été retenue.",),
            reperes=(("Motif indiqué", motif),) if motif else (),
            paragraphes_finaux=(
                "Rapprochez-vous de votre responsable si vous pensez qu'il "
                "s'agit d'une erreur : une nouvelle demande peut être déposée.",
            ),
        ),
    )


def reinitialisation_demandee(compte: Utilisateur, lien: str) -> Courriel:
    """Le titulaire a oublié son mot de passe et demande un lien."""
    return _rendre(
        compte,
        "Réinitialisation de votre mot de passe, Bordereau SOCADEL",
        Message(
            titre="Réinitialisez votre mot de passe",
            salutation=f"Bonjour {compte.nom_complet}",
            paragraphes=(
                "Une réinitialisation de mot de passe a été demandée pour le "
                f"compte « {compte.identifiant} ».",
            ),
            bouton=Bouton("Choisir un nouveau mot de passe", lien),
            mention_lien=(
                "Ce lien est valable deux heures et ne fonctionne qu'une fois. "
                "Si le bouton ne fonctionne pas, copiez cette adresse :"
            ),
            avertissement=(
                "Si vous n'êtes pas à l'origine de cette demande, ignorez ce "
                "message : votre mot de passe actuel reste valable."
            ),
        ),
    )


def reinitialisation_par_responsable(compte: Utilisateur) -> Courriel:
    """Un responsable a remis un mot de passe provisoire, de vive voix.

    Le mot de passe lui-même n'apparaît jamais ici : un courriel traverse des
    serveurs que nous ne maîtrisons pas, et reste lisible dans la boîte pendant
    des années.
    """
    return _rendre(
        compte,
        "Votre mot de passe a été réinitialisé, Bordereau SOCADEL",
        Message(
            titre="Votre mot de passe a été réinitialisé",
            salutation=f"Bonjour {compte.nom_complet}",
            paragraphes=(
                "Un responsable a réinitialisé le mot de passe du compte "
                f"« {compte.identifiant} ». Un mot de passe provisoire vous a "
                "été remis de vive voix, il ne figure pas dans ce message.",
                "Vous devrez le remplacer dès votre prochaine connexion.",
            ),
            avertissement=(
                "Si vous n'avez rien demandé, prévenez immédiatement votre "
                "administrateur : quelqu'un a peut-être obtenu l'accès à votre "
                "compte."
            ),
        ),
    )
