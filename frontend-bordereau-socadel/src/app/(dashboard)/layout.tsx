/** Layout des écrans authentifiés : tout passe par la coquille du back-office. */

import { Coquille } from "@shared/ui/Coquille";

export default function LayoutDashboard({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Coquille>{children}</Coquille>;
}
