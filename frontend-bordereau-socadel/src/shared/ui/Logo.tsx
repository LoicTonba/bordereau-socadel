/**
 * Marque SOCADEL.
 *
 * `LogoSocadel` affiche le lockup officiel (fichier fourni par le client) ;
 * `MarqueSocadel` en est la réduction carrée, l'éclair du « d'el », utilisée
 * partout où le lockup horizontal ne tient pas — barre latérale repliée,
 * favicon, en-tête compact.
 */

import Image from "next/image";

export function LogoSocadel({
  largeur = 168,
  className,
}: {
  largeur?: number;
  className?: string;
}) {
  return (
    <Image
      src="/LOGO_SOCADEL_CM.jpg"
      alt="SOCADEL, Société Camerounaise d'Electricité"
      width={largeur}
      height={Math.round((largeur * 465) / 1280)}
      priority
      className={className}
    />
  );
}

export function MarqueSocadel({
  taille = 32,
  className,
}: {
  taille?: number;
  className?: string;
}) {
  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: taille,
        height: taille,
        borderRadius: taille / 5,
        backgroundColor: "var(--color-socadel-600)",
      }}
    >
      <svg
        width={taille * 0.52}
        height={taille * 0.62}
        viewBox="0 0 75 149"
        fill="none"
        aria-hidden="true"
      >
        {/* Tracé de l'éclair, relevé sur le logotype fourni. */}
        <path d="M46 0 L4 84 H31 L20 149 L71 58 H41 Z" fill="white" />
      </svg>
    </span>
  );
}
