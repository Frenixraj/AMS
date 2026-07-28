import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { RecentActivity } from "@/types/dashboard";

interface RecentActivitiesProps {
  items: RecentActivity[];
}

function entityLink(entityType: string, entityId: string): string | null {
  if (entityType === "assets.Asset") return `/assets/${entityId}`;
  if (entityType === "approvals.AssetRequest") return `/approvals/${entityId}`;
  return null;
}

export function RecentActivities({ items }: RecentActivitiesProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">Recent activities</CardTitle>
        <CardDescription>Latest audit events across the platform</CardDescription>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent activity.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((item) => {
              const href = entityLink(item.entity_type, item.entity_id);
              return (
                <li
                  key={item.id}
                  className="flex flex-col gap-1 border-b pb-3 last:border-0 last:pb-0 sm:flex-row sm:items-start sm:justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary">{item.action}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {item.entity_type}
                        {href ? (
                          <>
                            {" · "}
                            <Link to={href} className="underline-offset-2 hover:underline">
                              #{item.entity_id}
                            </Link>
                          </>
                        ) : (
                          ` · #${item.entity_id}`
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {item.actor_email ?? "system"}
                    </p>
                  </div>
                  <time className="shrink-0 text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleString()}
                  </time>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
