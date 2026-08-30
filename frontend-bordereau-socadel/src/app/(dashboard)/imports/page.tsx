import type { Metadata } from "next";

import { EcranImportExport } from "@features/import-export/ui/EcranImportExport";

export const metadata: Metadata = { title: "Import / Export" };

export default function PageImports() {
  return <EcranImportExport />;
}
