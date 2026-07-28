import { Badge } from "@/components/ui/badge";
import type { TimelineEvent } from "@/types/approvals";

interface RequestTimelineProps {
  events: TimelineEvent[];
}

export function RequestTimeline({ events }: RequestTimelineProps) {
  if (!events.length) {
    return <p className="text-sm text-muted-foreground">No timeline events.</p>;
  }

  return (
    <ol className="space-y-4">
      {events.map((event, index) => {
        const isLast = index === events.length - 1;
        const done = event.status === "done";
        const current = event.status === "current";
        return (
          <li key={`${event.key}-${index}`} className="relative flex gap-3">
            {!isLast && (
              <span
                className="absolute left-[9px] top-5 h-[calc(100%-8px)] w-px bg-border"
                aria-hidden
              />
            )}
            <span
              className={[
                "relative z-10 mt-1 h-2.5 w-2.5 shrink-0 rounded-full",
                done ? "bg-emerald-600" : "",
                current ? "bg-amber-500 ring-4 ring-amber-100" : "",
                !done && !current ? "bg-muted-foreground/40" : "",
              ].join(" ")}
            />
            <div className="flex-1 space-y-1 pb-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-medium">{event.label}</p>
                {current && <Badge variant="warning">Current</Badge>}
              </div>
              <p className="text-xs text-muted-foreground">{event.detail}</p>
              <p className="text-xs text-muted-foreground">
                {event.actor ? `${event.actor} · ` : ""}
                {event.at ? new Date(event.at).toLocaleString() : "—"}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
