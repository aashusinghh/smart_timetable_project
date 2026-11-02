export type RoleCode = 'SUPER_ADMIN' | 'BRANCH_COORDINATOR' | 'PROFESSOR';

export interface Role {
  id: number;
  code: RoleCode;
  name: string;
  description?: string;
}

export interface BranchSummary {
  id: number;
  code: string;
  name: string;
  degree_name: string;
}

export interface DepartmentSummary {
  id: number;
  code: string;
  name: string;
}

export interface UserRoleAssignment {
  id: number;
  role: Role;
  branch?: BranchSummary | null;
  created_at: string;
}

export interface ProfessorProfile {
  id: number;
  designation: string;
  department: DepartmentSummary;
  max_hours_per_day: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  employee_code?: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  roles: RoleCode[];
  role_assignments: UserRoleAssignment[];
  professor_profile?: ProfessorProfile | null;
  created_at: string;
  updated_at?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse extends AuthTokens {
  user: User;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  description?: string;
  branches_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Branch {
  id: number;
  department: number;
  department_name?: string;
  department_code?: string;
  code: string;
  name: string;
  degree_name: string;
  max_semesters: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

