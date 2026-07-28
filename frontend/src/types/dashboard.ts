export interface DashboardWidgets {
  total_assets: number;
  allocated: number;
  available: number;
  maintenance: number;
  lost: number;
  requested: number;
  retired: number;
  warranty_expiring: number;
  warranty_window_days: number;
}

export interface ChartSlice {
  name: string;
  value: number;
}

export interface MonthlyAllocationPoint {
  month: string;
  month_key: string;
  allocations: number;
}

export interface RecentActivity {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string;
  actor_email: string | null;
  changes: Record<string, unknown>;
  created_at: string;
}

export interface DashboardSummary {
  widgets: DashboardWidgets;
  charts: {
    category_distribution: ChartSlice[];
    department_distribution: ChartSlice[];
    monthly_allocations: MonthlyAllocationPoint[];
  };
  recent_activities: RecentActivity[];
  generated_at: string;
}
