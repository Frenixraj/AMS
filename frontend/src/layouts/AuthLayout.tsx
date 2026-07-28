import { Outlet } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>AssetFlow</CardTitle>
          <CardDescription>Asset Management System</CardDescription>
        </CardHeader>
        <CardContent>
          <Outlet />
        </CardContent>
      </Card>
    </div>
  );
}
