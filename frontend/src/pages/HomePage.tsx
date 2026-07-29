import { Link } from "react-router-dom";

import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";

export function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gradient-to-b from-slate-50 via-sky-50/50 to-slate-100 p-4">
      <Card className="w-full max-w-lg shadow-sm">
        <CardHeader className="items-center text-center">
          <Logo imgClassName="h-16" showTagline className="items-center" />
          <CardDescription className="pt-3">
            Smart asset management with QR tracking, approval workflows, maintenance, and analytics.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap justify-center gap-3">
          <Button asChild>
            <Link to="/login">Sign in</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/dashboard">Open dashboard</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link to="/assets/scan">Scan QR</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
