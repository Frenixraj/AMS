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
import { isAdminOrIT } from "@/utils/roles";

export function EmployeesPage() {
  const { user } = useAuth();
  const canManage = isAdminOrIT(user);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [availableAssets, setAvailableAssets] = useState<AssetListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deptForm, setDeptForm] = useState({ name: "", code: "" });
  const [assignForm, setAssignForm] = useState({ asset_id: "", employee_id: "" });
  const [empForm, setEmpForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role: "EMPLOYEE",
    department: "",
    employee_code: "",
    job_title: "",
    phone: "",
  });

  const load = useCallback(async () => {
    setError(null);
    try {
      const [emps, deps, assigns, assets] = await Promise.all([
        employeeService.list({ page_size: 100 }),
        employeeService.listDepartments(),
        assignmentService.list({ status: "ACTIVE", page_size: 50 }),
        canManage
          ? assetService.list({ status: "AVAILABLE", page: 1 })
          : Promise.resolve({
              results: [] as AssetListItem[],
              count: 0,
              next: null,
              previous: null,
            }),
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

  const createEmployee = async () => {
    if (
      !empForm.email.trim() ||
      !empForm.password ||
      !empForm.department ||
      !empForm.employee_code.trim()
    ) {
      return;
    }
    try {
      await employeeService.provision({
        email: empForm.email.trim().toLowerCase(),
        password: empForm.password,
        first_name: empForm.first_name.trim() || undefined,
        last_name: empForm.last_name.trim() || undefined,
        role: empForm.role,
        department: Number(empForm.department),
        employee_code: empForm.employee_code.trim().toUpperCase(),
        job_title: empForm.job_title.trim() || undefined,
        phone: empForm.phone.trim() || undefined,
      });
      setEmpForm({
        email: "",
        password: "",
        first_name: "",
        last_name: "",
        role: "EMPLOYEE",
        department: "",
        employee_code: "",
        job_title: "",
        phone: "",
      });
      await load();
    } catch {
      setError("Could not create employee (email/code may already exist).");
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
          Add people with a department, then assign assets to them.
        </p>
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

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
          <CardContent className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Employee directory</caption>
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th scope="col" className="py-2 pr-3">
                      Code
                    </th>
                    <th scope="col" className="py-2 pr-3">
                      Name
                    </th>
                    <th scope="col" className="py-2">
                      Department
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((e) => (
                    <tr key={e.id} className="border-b last:border-0">
                      <td className="py-2 pr-3 font-mono text-xs">{e.employee_code}</td>
                      <td className="py-2 pr-3">
                        <div>{e.full_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {e.email} · {e.user_role}
                        </div>
                      </td>
                      <td className="py-2">{e.department_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {canManage && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Add employee</CardTitle>
            <CardDescription>
              Creates a login account and employee profile so you can assign assets and test as that
              user.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="emp-email">Email</Label>
              <Input
                id="emp-email"
                type="email"
                value={empForm.email}
                onChange={(e) => setEmpForm({ ...empForm, email: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="emp-password">Temp password</Label>
              <Input
                id="emp-password"
                type="password"
                value={empForm.password}
                onChange={(e) => setEmpForm({ ...empForm, password: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="emp-fn">First name</Label>
              <Input
                id="emp-fn"
                value={empForm.first_name}
                onChange={(e) => setEmpForm({ ...empForm, first_name: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="emp-ln">Last name</Label>
              <Input
                id="emp-ln"
                value={empForm.last_name}
                onChange={(e) => setEmpForm({ ...empForm, last_name: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="emp-role">Role</Label>
              <select
                id="emp-role"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={empForm.role}
                onChange={(e) => setEmpForm({ ...empForm, role: e.target.value })}
              >
                <option value="EMPLOYEE">Employee</option>
                <option value="MANAGER">Manager</option>
                <option value="IT_TEAM">IT Team</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="emp-dept">Department</Label>
              <select
                id="emp-dept"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={empForm.department}
                onChange={(e) => setEmpForm({ ...empForm, department: e.target.value })}
              >
                <option value="">Select department</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.code} — {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="emp-code">Employee code</Label>
              <Input
                id="emp-code"
                value={empForm.employee_code}
                onChange={(e) => setEmpForm({ ...empForm, employee_code: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="emp-title">Job title</Label>
              <Input
                id="emp-title"
                value={empForm.job_title}
                onChange={(e) => setEmpForm({ ...empForm, job_title: e.target.value })}
              />
            </div>
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="emp-phone">Phone</Label>
              <Input
                id="emp-phone"
                value={empForm.phone}
                onChange={(e) => setEmpForm({ ...empForm, phone: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <Button onClick={() => void createEmployee()}>Create employee + login</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Active assignments</CardTitle>
          <CardDescription>Direct IT assign / return outside approval workflow</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {canManage && (
            <div className="grid gap-2 md:grid-cols-3">
              <div className="space-y-1">
                <Label htmlFor="assign-asset">Asset</Label>
                <select
                  id="assign-asset"
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
                <Label htmlFor="assign-employee">Employee</Label>
                <select
                  id="assign-employee"
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
                    onClick={() => void assignmentService.returnAsset(a.id).then(() => load())}
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
