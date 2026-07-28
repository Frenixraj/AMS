import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AssetRequestListItem, RequestStatus } from "@/types/approvals";

const STATUS_VARIANT: Record<
  RequestStatus,
  "success" | "warning" | "danger" | "muted" | "default" | "secondary"
> = {
  PENDING: "warning",
  APPROVED: "default",
  REJECTED: "danger",
  CANCELLED: "muted",
  FULFILLED: "success",
};

interface RequestTableProps {
  requests: AssetRequestListItem[];
}

export function RequestTable({ requests }: RequestTableProps) {
  if (requests.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">
        No requests match your filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="border-b bg-muted/40">
          <tr>
            <th className="px-4 py-3 font-medium">Request</th>
            <th className="px-4 py-3 font-medium">Requester</th>
            <th className="px-4 py-3 font-medium">Item</th>
            <th className="px-4 py-3 font-medium">Priority</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((item) => (
            <tr key={item.id} className="border-b last:border-0 hover:bg-muted/20">
              <td className="px-4 py-3">
                <div className="font-mono text-xs">{item.request_number}</div>
                <div className="text-xs text-muted-foreground">
                  {new Date(item.created_at).toLocaleString()}
                </div>
              </td>
              <td className="px-4 py-3">
                <div>{item.requested_by_email}</div>
                <div className="text-xs text-muted-foreground">{item.department_name}</div>
              </td>
              <td className="px-4 py-3">
                {item.asset_tag ?? item.category_name ?? "—"}
              </td>
              <td className="px-4 py-3">{item.priority}</td>
              <td className="px-4 py-3">
                <Badge variant={STATUS_VARIANT[item.status]}>
                  {item.status.replaceAll("_", " ")}
                </Badge>
              </td>
              <td className="px-4 py-3 text-right">
                <Button asChild size="sm" variant="outline">
                  <Link to={`/approvals/${item.id}`}>Open</Link>
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
