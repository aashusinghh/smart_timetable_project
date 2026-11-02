import { api } from './api';
import { Department, Branch } from '../types';

export interface CreateDepartmentInput {
  code: string;
  name: string;
  description?: string;
  is_active?: boolean;
}

export interface CreateBranchInput {
  department: number;
  code: string;
  name: string;
  degree_name: string;
  max_semesters: number;
  is_active?: boolean;
}

export const academicsService = {
  // Departments
  async getDepartments(): Promise<Department[]> {
    const response = await api.get<{ results?: Department[] } | Department[]>('/departments/');
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data.results || [];
  },

  async createDepartment(data: CreateDepartmentInput): Promise<Department> {
    const response = await api.post<Department>('/departments/', data);
    return response.data;
  },

  async updateDepartment(id: number, data: Partial<CreateDepartmentInput>): Promise<Department> {
    const response = await api.patch<Department>(`/departments/${id}/`, data);
    return response.data;
  },

  async deleteDepartment(id: number): Promise<void> {
    await api.delete(`/departments/${id}/`);
  },

  // Branches
  async getBranches(departmentId?: number): Promise<Branch[]> {
    const params: Record<string, any> = {};
    if (departmentId) {
      params.department = departmentId;
    }
    const response = await api.get<{ results?: Branch[] } | Branch[]>('/branches/', { params });
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data.results || [];
  },

  async createBranch(data: CreateBranchInput): Promise<Branch> {
    const response = await api.post<Branch>('/branches/', data);
    return response.data;
  },

  async updateBranch(id: number, data: Partial<CreateBranchInput>): Promise<Branch> {
    const response = await api.patch<Branch>(`/branches/${id}/`, data);
    return response.data;
  },

  async deleteBranch(id: number): Promise<void> {
    await api.delete(`/branches/${id}/`);
  },
};

