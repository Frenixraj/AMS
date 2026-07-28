import { apiClient } from "@/services/api";
import type { PaginatedResponse } from "@/types/assets";

export interface Department {
  id: number;
  name: string;
  code: string;
  description: string;
  manager: number | null;
  manager_email: string | null;
  employee_count: number;
  is_active: boolean;
}

export interface Employee {
  id: number;
  user: number;
  email: string;
  full_name: string;
  user_role: string;
  department: number;
  department_name: string;
  employee_code: string;
  job_title: string;
  phone: string;
  hire_date: string | null;
  is_active: boolean;
}

export const employeeService = {
  async listDepartments(): Promise<PaginatedResponse<Department>> {
    const { data } = await apiClient.get("/employees/departments/", {
      params: { page_size: 100, is_active: true },
    });
    return data;
  },
  async createDepartment(payload: {
    name: string;
    code: string;
    description?: string;
    manager?: number | null;
  }): Promise<Department> {
    const { data } = await apiClient.post("/employees/departments/", payload);
    return data;
  },
  async list(params: Record<string, string | number | boolean> = {}): Promise<PaginatedResponse<Employee>> {
    const { data } = await apiClient.get("/employees/", { params });
    return data;
  },
  async create(payload: {
    user: number;
    department: number;
    employee_code: string;
    job_title?: string;
    phone?: string;
    hire_date?: string;
  }): Promise<Employee> {
    const { data } = await apiClient.post("/employees/", payload);
    return data;
  },
  async provision(payload: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    role?: string;
    department: number;
    employee_code: string;
    job_title?: string;
    phone?: string;
  }): Promise<Employee> {
    const { data } = await apiClient.post("/employees/provision/", payload);
    return data;
  },
};
