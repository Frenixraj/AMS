import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatWidgetProps {
  title: string;
  value: number;
  hint?: string;
  icon: LucideIcon;
  tone?: "default" | "success" | "warning" | "danger" | "info";
}

const TONE_CLASSES: Record<NonNullable<StatWidgetProps["tone"]>, string> = {
  default: "bg-slate-100 text-slate-700",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-red-100 text-red-700",
  info: "bg-sky-100 text-sky-700",
};

export function StatWidget({
  title,
  value,
  hint,
  icon: Icon,
  tone = "default",
}: StatWidgetProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <span className={cn("rounded-md p-2", TONE_CLASSES[tone])}>
          <Icon className="h-4 w-4" />
        </span>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold tracking-tight tabular-nums">
          {value.toLocaleString()}
        </div>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}
