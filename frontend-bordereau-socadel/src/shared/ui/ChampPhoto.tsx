/**
 * Champ de dépôt d'une photo de profil.
 *
 * Le dépôt et l'enregistrement sont deux gestes distincts : la photo part vers
 * l'API dès la sélection et revient sous forme d'URL, que le formulaire porte
 * ensuite. On voit donc l'aperçu avant de valider, et abandonner le formulaire
 * n'écrit rien sur la fiche.
 */

"use client";

import { useRef, useState } from "react";

import { useT } from "@core/i18n/PreferencesProvider";
import { useDeposerPhoto } from "@features/agents/application/hooks";
import { ErreurApi } from "@infra/http/client";

import { Avatar } from "./Avatar";
import { URL_API } from "@infra/http/client";

const FORMATS = "image/jpeg,image/png,image/webp";

/** Les URL renvoyées par l'API sont relatives à son hôte, pas à celui du front. */
export function urlAbsolue(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${URL_API.replace(/\/api\/v\d+$/, "")}${url}`;
}

export function ChampPhoto({
  libelle,
  aide,
  nom,
  url,
  onChange,
}: {
  libelle: string;
  aide?: string;
  nom: string;
  url: string | null;
  onChange: (url: string | null) => void;
}) {
  const t = useT();
  const champ = useRef<HTMLInputElement>(null);
  const deposer = useDeposerPhoto();
  const [erreur, setErreur] = useState<string | null>(null);

  async function selectionner(fichier: File) {
    setErreur(null);
    try {
      const resultat = await deposer.mutateAsync(fichier);
      onChange(resultat.url);
    } catch (exception) {
      setErreur(
        exception instanceof ErreurApi
          ? exception.message
          : t("commun.erreurGenerique"),
      );
    } finally {
      // Réinitialisé pour qu'un même fichier redéposé déclenche bien un
      // nouvel événement `change`.
      if (champ.current) champ.current.value = "";
    }
  }

  return (
    <div className="space-y-1.5">
      <span className="block text-sm font-medium text-[var(--texte-doux)]">
        {libelle}
      </span>

      <div className="flex items-center gap-3">
        <Avatar nom={nom} url={urlAbsolue(url)} taille={56} />

        <div className="flex flex-col gap-1.5">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => champ.current?.click()}
              disabled={deposer.isPending}
              className="rounded-lg border border-[var(--bordure-forte)] px-3 py-1.5 text-xs font-medium hover:bg-[var(--fond-survol)] disabled:opacity-55"
            >
              {deposer.isPending ? t("commun.chargement") : t("commun.modifier")}
            </button>

            {url && (
              <button
                type="button"
                onClick={() => onChange(null)}
                className="rounded-lg px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
              >
                {t("commun.supprimer")}
              </button>
            )}
          </div>

          {erreur ? (
            <p className="text-xs text-red-600">{erreur}</p>
          ) : (
            aide && (
              <p className="text-xs text-[var(--texte-tres-doux)]">{aide}</p>
            )
          )}
        </div>
      </div>

      <input
        ref={champ}
        type="file"
        accept={FORMATS}
        className="sr-only"
        onChange={(evenement) => {
          const fichier = evenement.target.files?.[0];
          if (fichier) void selectionner(fichier);
        }}
      />
    </div>
  );
}
