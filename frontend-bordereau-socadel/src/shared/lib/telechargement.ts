/**
 * Déclenchement d'un téléchargement depuis un blob reçu de l'API.
 *
 * Le fichier arrive par `fetch` (il faut l'en-tête d'authentification) : il
 * n'existe donc aucune URL directe à mettre dans un lien. On passe par une URL
 * objet éphémère, révoquée aussitôt pour ne pas retenir le blob en mémoire.
 */

export function telechargerBlob(blob: Blob, nomFichier: string): void {
  const url = URL.createObjectURL(blob);
  const lien = document.createElement("a");

  lien.href = url;
  lien.download = nomFichier;
  document.body.appendChild(lien);
  lien.click();
  lien.remove();

  // Le navigateur a besoin d'un tour de boucle pour amorcer le téléchargement
  // avant que l'URL ne devienne invalide.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
