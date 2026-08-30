import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Sans borne explicite, Turbopack remonte jusqu'au `pnpm-workspace.yaml` du
  // répertoire personnel et englobe tout le disque de l'utilisateur.
  turbopack: { root: path.join(__dirname, "..") },
  // L'API FastAPI est le seul backend : on la déclare ici pour que le client
  // HTTP n'ait qu'une variable à lire, en dev comme en production.
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  },
};

export default nextConfig;
