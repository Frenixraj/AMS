import { Outlet } from "react-router-dom";

import { Logo } from "@/components/brand/Logo";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-50 via-sky-50/40 to-slate-100 p-4">
      <Card className="w-full max-w-md shadow-sm">
        <CardHeader className="items-center text-center">
          <Logo imgClassName="h-14" showTagline className="items-center" />
          <CardDescription className="pt-2">Sign in to manage your assets</CardDescription>
        </CardHeader>
        <CardContent>
          <Outlet />
        </CardContent>
      </Card>
    </div>
  );
}
