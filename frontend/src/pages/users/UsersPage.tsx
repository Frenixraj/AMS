import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authService, type ManagedUser } from "@/services/auth.service";

const ROLES = ["ADMIN", "IT_TEAM", "MANAGER", "EMPLOYEE"] as const;

export function UsersPage() {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role: "EMPLOYEE",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await authService.listUsers();
      setUsers(data.results);
    } catch {
      setError("Failed to load users. Admin access required.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const createUser = async () => {
    if (!form.email.trim() || !form.password) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      await authService.createUser({
        email: form.email.trim().toLowerCase(),
        password: form.password,
        first_name: form.first_name.trim() || undefined,
        last_name: form.last_name.trim() || undefined,
        role: form.role,
      });
      setForm({
        email: "",
        password: "",
        first_name: "",
        last_name: "",
        role: "EMPLOYEE",
      });
      setSuccess("User created. They can log in with the email and password you set.");
      await load();
    } catch {
      setError("Could not create user (email may already exist, or password too short).");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Users</h1>
        <p className="text-sm text-muted-foreground">
          Admin-only: create login accounts and assign roles.
        </p>
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
          <CardTitle className="text-base">Create user</CardTitle>
          <CardDescription>
            After creating an Employee-role user, link them on the Employees page if they need asset
            assignment.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="user-email">Email</Label>
            <Input
              id="user-email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="user-password">Temporary password</Label>
            <Input
              id="user-password"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="user-fn">First name</Label>
            <Input
              id="user-fn"
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="user-ln">Last name</Label>
            <Input
              id="user-ln"
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            />
          </div>
          <div className="space-y-1 sm:col-span-2">
            <Label htmlFor="user-role">Role</Label>
            <select
              id="user-role"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
            >
              {ROLES.map((role) => (
                <option key={role} value={role}>
                  {role.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2">
            <Button disabled={submitting} onClick={() => void createUser()}>
              {submitting ? "Creating…" : "Create user"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">All users</CardTitle>
          <CardDescription>{users.length} accounts</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">User accounts</caption>
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th scope="col" className="py-2 pr-3">
                      Name
                    </th>
                    <th scope="col" className="py-2 pr-3">
                      Email
                    </th>
                    <th scope="col" className="py-2 pr-3">
                      Role
                    </th>
                    <th scope="col" className="py-2 pr-3">
                      Active
                    </th>
                    <th scope="col" className="py-2">
                      Employee profile
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b last:border-0">
                      <td className="py-2 pr-3">{u.full_name}</td>
                      <td className="py-2 pr-3">{u.email}</td>
                      <td className="py-2 pr-3 font-mono text-xs">{u.role}</td>
                      <td className="py-2 pr-3">{u.is_active ? "Yes" : "No"}</td>
                      <td className="py-2">{u.has_employee_profile ? "Yes" : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
