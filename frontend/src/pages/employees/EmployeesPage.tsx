import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { assignmentService, type Assignment } from "@/services/assignment.service";
import { employeeService, type Department, type Employee } from "@/services/employee.service";
import { assetService } from "@/services/asset.service";
import type { AssetListItem } from "@/types/assets";

export function EmployeesPage() {
  const { user } = useAuth();
  const canManage = user?.role === "ADMIN" || user?.role === "IT_TEAM";
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [availableAssets, setAvailableAssets] = useState<AssetListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deptForm, setDeptForm] = useState({ name: "", code: "" });
  const [assignForm, setAssignForm] = useState({ asset_id: "", employee_id: "" });

  const load = useCallback(async () => {
    setError(null);
    try {
      const [emps, deps, assigns, assets] = await Promise.all([
        employeeService.list({ page_size: 100 }),
        employeeService.listDepartments(),
        assignmentService.list({ status: "ACTIVE", page_size: 50 }),
        canManage
          ? assetService.list({ status: "AVAILABLE", page: 1 })
          : Promise.resolve({ results: [] as AssetListItem[], count: 0, next: null, previous: null }),
      ]);
      setEmployees(emps.results);
      setDepartments(deps.results);
      setAssignments(assigns.results);
      setAvailableAssets(assets.results);
    } catch {
      setError("Failed to load employees.");
    }
  }, [canManage]);

  useEffect(() => {
    void load();
  }, [load]);

  const createDept = async () => {
    try {
      await employeeService.createDepartment({
        name: deptForm.name,
        code: deptForm.code.toUpperCase(),
      });
      setDeptForm({ name: "", code: "" });
      await load();
    } catch {
      setError("Could not create department.");
    }
  };

  const assign = async () => {
    if (!assignForm.asset_id || !assignForm.employee_id) return;
    try {
      await assignmentService.assign({
        asset_id: Number(assignForm.asset_id),
        employee_id: Number(assignForm.employee_id),
      });
      setAssignForm({ asset_id: "", employee_id: "" });
      await load();
    } catch {
      setError("Assignment failed.");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Employees</h1>
        <p className="text-sm text-muted-foreground">
          Departments, people, and active asset assignments.
        </p>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Departments</CardTitle>
            <CardDescription>{departments.length} departments</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2 text-sm">
              {departments.map((d) => (
                <li key={d.id} className="flex justify-between border-b pb-2">
                  <span>
                    <span className="font-mono text-xs">{d.code}</span> · {d.name}
                  </span>
                  <span className="text-muted-foreground">{d.employee_count} people</span>
                </li>
              ))}
            </ul>
            {canManage && (
              <div className="grid gap-2 sm:grid-cols-3">
                <Input
                  placeholder="Name"
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                />
                <Input
                  placeholder="Code"
                  value={deptForm.code}
                  onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value })}
                />
                <Button onClick={() => void createDept()}>Add department</Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Directory</CardTitle>
            <CardDescription>{employees.length} employees</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th className="py-2 pr-3">Code</th>
                    <th className="py-2 pr-3">Name</th>
                    <th className="py-2">Department</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((e) => (
                    <tr key={e.id} className="border-b last:border-0">
                      <td className="py-2 pr-3 font-mono text-xs">{e.employee_code}</td>
                      <td className="py-2 pr-3">
                        <div>{e.full_name}</div>
                        <div className="text-xs text-muted-foreground">{e.email}</div>
                      </td>
                      <td className="py-2">{e.department_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {canManage && (
              <p className="mt-3 text-xs text-muted-foreground">
                Create employee profiles via API/admin (link User → Department). Use assign below for
                direct IT allocation.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Active assignments</CardTitle>
          <CardDescription>Direct IT assign / return outside approval workflow</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {canManage && (
            <div className="grid gap-2 md:grid-cols-3">
              <div className="space-y-1">
                <Label>Asset</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={assignForm.asset_id}
                  onChange={(e) => setAssignForm({ ...assignForm, asset_id: e.target.value })}
                >
                  <option value="">Select available asset</option>
                  {availableAssets.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.asset_tag} — {a.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Employee</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={assignForm.employee_id}
                  onChange={(e) => setAssignForm({ ...assignForm, employee_id: e.target.value })}
                >
                  <option value="">Select employee</option>
                  {employees.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.employee_code} — {e.full_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-end">
                <Button onClick={() => void assign()}>Assign asset</Button>
              </div>
            </div>
          )}
          <ul className="space-y-2 text-sm">
            {assignments.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
                <span>
                  <span className="font-mono text-xs">{a.asset_tag}</span> → {a.employee_code} (
                  {a.employee_email})
                </span>
                {canManage && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      void assignmentService.returnAsset(a.id).then(() => load())
                    }
                  >
                    Return
                  </Button>
                )}
              </li>
            ))}
            {assignments.length === 0 && (
              <li className="text-muted-foreground">No active assignments.</li>
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
