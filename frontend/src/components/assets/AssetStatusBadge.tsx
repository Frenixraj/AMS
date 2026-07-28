import type { AssetStatus } from "@/types/assets";

import { Badge } from "@/components/ui/badge";

const STATUS_VARIANT: Record<
  AssetStatus,
  "success" | "warning" | "danger" | "muted" | "secondary" | "default"
> = {
  AVAILABLE: "success",
  REQUESTED: "warning",
  ALLOCATED: "default",
  MAINTENANCE: "warning",
  RETIRED: "muted",
  LOST: "danger",
};

export function AssetStatusBadge({ status }: { status: AssetStatus }) {
  return (
    <Badge variant={STATUS_VARIANT[status] ?? "secondary"}>
      {status.replaceAll("_", " ")}
    </Badge>
  );
}
