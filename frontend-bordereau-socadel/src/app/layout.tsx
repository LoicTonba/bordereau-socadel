/**
 * Layout racine.
 *
 * Le routage est la seule responsabilité du dossier `app/` : la logique vit
 * dans `features/`, les briques d'interface dans `shared/`.
 */

import type { Metadata, Viewport } from "next";

import { Fournisseurs } from "./providers";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: {
    default: "Bordereau SOCADEL",
    template: "%s · Bordereau SOCADEL",
  },
  description:
    "Bordereau intelligent de collecte de numéros WhatsApp — SOCADEL, opéré par NEXT LTD.",
  applicationName: "Bordereau SOCADEL",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon.png", type: "image/png", sizes: "32x32" },
      { url: "/icon-192.png", type: "image/png", sizes: "192x192" },
    ],
    apple: "/apple-icon.png",
  },
  // Le back-office n'a pas vocation à être indexé.
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#1a76b9" },
    { media: "(prefers-color-scheme: dark)", color: "#0b1220" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="min-h-dvh antialiased">
        <Fournisseurs>{children}</Fournisseurs>
      </body>
    </html>
  );
}
