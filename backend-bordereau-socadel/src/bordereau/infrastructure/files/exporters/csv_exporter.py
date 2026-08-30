"""Export CSV du bordereau. Implémente le port `ExportateurCsv`."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence

from ....domain.entities import LigneBordereau

EN_TETES = (
    "SERVICE_NO",
    "NOMS",
    "REF_GEO",
    "ITINERAIRE",
    "METER_NO",
    "NUMERO_TELEPHONE",
    "STATUT",
    "RESPONSABLE",
    "VERDICT",
    "DATE_COLLECTE",
    "OBSERVATION",
)


class ExportateurCsvStandard:
    """Sérialise les lignes au format attendu par les outils SOCADEL."""

    #: Excel francophone ouvre nativement les CSV séparés par point-virgule ;
    #: avec une virgule, tout atterrit dans une seule colonne.
    SEPARATEUR = ";"

    def exporter_bordereau(self, lignes: Sequence[LigneBordereau]) -> bytes:
        tampon = io.StringIO()
        redacteur = csv.writer(
            tampon, delimiter=self.SEPARATEUR, quoting=csv.QUOTE_MINIMAL
        )
        redacteur.writerow(EN_TETES)

        for ligne in lignes:
            redacteur.writerow(
                (
                    ligne.service_no.valeur,
                    ligne.nom_client or "",
                    ligne.ref_geo.valeur if ligne.ref_geo else "",
                    ligne.code_itineraire.valeur if ligne.code_itineraire else "",
                    ligne.numero_compteur or "",
                    ligne.numero_collecte.valeur if ligne.numero_collecte else "",
                    ligne.statut.value,
                    ligne.responsable.value if ligne.responsable else "",
                    ligne.verdict.value,
                    ligne.date_collecte.strftime("%d/%m/%Y"),
                    ligne.observation or "",
                )
            )

        # BOM UTF-8 : sans lui, Excel affiche « SANGMÉLIMA » en mojibake.
        return tampon.getvalue().encode("utf-8-sig")
