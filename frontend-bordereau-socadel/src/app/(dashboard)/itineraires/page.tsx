import type { Metadata } from "next";

import { EcranItineraires } from "@features/itineraires/ui/EcranItineraires";

export const metadata: Metadata = { title: "Itinéraires" };

export default function PageItineraires() {
  return <EcranItineraires />;
}
