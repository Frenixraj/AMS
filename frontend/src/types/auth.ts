export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role?: "ADMIN" | "ASSET_MANAGER" | "MANAGER" | "EMPLOYEE" | "IT_TEAM";
  phone?: string;
  address?: string;
  profile_picture_url?: string | null;
  is_active?: boolean;
  employee_profile?: {
    id: number;
    employee_code: string;
    department_id: number;
    department_name: string;
    job_title: string;
    phone?: string;
    is_active: boolean;
  } | null;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
