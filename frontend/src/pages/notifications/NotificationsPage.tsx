import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { notificationService, type AppNotification } from "@/services/notification.service";

export function NotificationsPage() {
  const [items, setItems] = useState<AppNotification[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await notificationService.list({ page_size: 50 });
      setItems(data.results);
    } catch {
      setError("Failed to load notifications.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Notifications</h1>
          <p className="text-sm text-muted-foreground">In-app alerts from workflow events.</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void notificationService.markAllRead().then(load)}
        >
          Mark all read
        </Button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Inbox</CardTitle>
          <CardDescription>{items.length} notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {items.map((n) => (
            <div
              key={n.id}
              className={`rounded-md border p-3 text-sm ${n.is_read ? "opacity-70" : "bg-muted/30"}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{n.notification_type}</Badge>
                  <span className="font-medium">{n.title}</span>
                </div>
                <time className="text-xs text-muted-foreground">
                  {new Date(n.created_at).toLocaleString()}
                </time>
              </div>
              <p className="mt-1 text-muted-foreground">{n.message}</p>
              <div className="mt-2 flex gap-2">
                {n.link && (
                  <Button asChild size="sm" variant="outline">
                    <Link to={n.link} onClick={() => void notificationService.markRead(n.id)}>
                      Open
                    </Link>
                  </Button>
                )}
                {!n.is_read && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void notificationService.markRead(n.id).then(load)}
                  >
                    Mark read
                  </Button>
                )}
              </div>
            </div>
          ))}
          {items.length === 0 && (
            <p className="text-sm text-muted-foreground">No notifications yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
