import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { authService } from "@/services/auth.service";

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    address: "",
  });
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!user) return;
    setForm({
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      phone: user.phone || user.employee_profile?.phone || "",
      address: user.address || "",
    });
  }, [user]);

  const save = async () => {
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const fd = new FormData();
      fd.append("first_name", form.first_name);
      fd.append("last_name", form.last_name);
      fd.append("phone", form.phone);
      fd.append("address", form.address);
      if (file) fd.append("profile_picture", file);
      await authService.updateProfile(fd);
      await refreshUser();
      setFile(null);
      setSuccess("Profile updated.");
    } catch {
      setError("Could not update profile.");
    } finally {
      setBusy(false);
    }
  };

  if (!user) {
    return <p className="text-sm text-muted-foreground">Loading profile…</p>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground">Your picture, contact details, and credentials.</p>
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
      {success && (
        <p className="text-sm text-emerald-700" role="status">
          {success}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Account</CardTitle>
          <CardDescription>
            Role: {user.role?.replaceAll("_", " ")} · Email (login): {user.email}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            {user.profile_picture_url ? (
              <img
                src={user.profile_picture_url}
                alt="Profile"
                className="h-20 w-20 rounded-full object-cover border"
              />
            ) : (
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted text-xl font-medium">
                {(user.first_name || user.email).charAt(0).toUpperCase()}
              </div>
            )}
            <div className="space-y-1">
              <Label htmlFor="pic">Profile picture</Label>
              <Input
                id="pic"
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="fn">First name</Label>
              <Input
                id="fn"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="ln">Last name</Label>
              <Input
                id="ln"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </div>
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="address">Address</Label>
              <Textarea
                id="address"
                rows={3}
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </div>
          </div>

          {user.employee_profile && (
            <div className="rounded-md border bg-muted/30 p-3 text-sm space-y-1">
              <p>
                <span className="text-muted-foreground">Employee code:</span>{" "}
                {user.employee_profile.employee_code}
              </p>
              <p>
                <span className="text-muted-foreground">Department:</span>{" "}
                {user.employee_profile.department_name}
              </p>
              <p>
                <span className="text-muted-foreground">Job title:</span>{" "}
                {user.employee_profile.job_title || "—"}
              </p>
            </div>
          )}

          <Button disabled={busy} onClick={() => void save()}>
            {busy ? "Saving…" : "Save profile"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
