import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChartSlice, MonthlyAllocationPoint } from "@/types/dashboard";

const CHART_COLORS = [
  "#0f766e",
  "#0369a1",
  "#b45309",
  "#be123c",
  "#4338ca",
  "#15803d",
  "#a16207",
  "#334155",
];

interface CategoryChartProps {
  data: ChartSlice[];
}

export function CategoryDistributionChart({ data }: CategoryChartProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">Category distribution</CardTitle>
        <CardDescription>Assets by category</CardDescription>
      </CardHeader>
      <CardContent className="h-[280px]">
        {data.length === 0 ? (
          <EmptyChart />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={2}
              >
                {data.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => [value, "Assets"]} />
              <Legend verticalAlign="bottom" height={36} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

interface DepartmentChartProps {
  data: ChartSlice[];
}

export function DepartmentDistributionChart({ data }: DepartmentChartProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">Department distribution</CardTitle>
        <CardDescription>Active allocations by department</CardDescription>
      </CardHeader>
      <CardContent className="h-[280px]">
        {data.length === 0 ? (
          <EmptyChart message="No active allocations yet." />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" name="Allocations" radius={[4, 4, 0, 0]} fill="#0369a1" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

interface MonthlyChartProps {
  data: MonthlyAllocationPoint[];
}

export function MonthlyAllocationChart({ data }: MonthlyChartProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">Monthly allocation</CardTitle>
        <CardDescription>Assignments over the last 12 months</CardDescription>
      </CardHeader>
      <CardContent className="h-[300px]">
        {data.length === 0 ? (
          <EmptyChart />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="allocations"
                name="Allocations"
                stroke="#0f766e"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

function EmptyChart({ message = "No data available." }: { message?: string }) {
  return (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      {message}
    </div>
  );
}
