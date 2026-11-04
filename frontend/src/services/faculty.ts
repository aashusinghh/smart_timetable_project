import { api } from './api';
import { ProfessorListItem, ProfessorUnavailability } from '../types';

export interface CreateProfessorInput {
  email: string;
  full_name: string;
  employee_code?: string;
  password?: string;
  department: number;
  designation: string;
  max_hours_per_day: number;
}

export const facultyService = {
  getProfessors: async (departmentId?: number): Promise<ProfessorListItem[]> => {
    const params = departmentId ? { department: departmentId } : {};
    const res = await api.get<{ results: ProfessorListItem[] } | ProfessorListItem[]>('/professors/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  createProfessor: async (data: CreateProfessorInput): Promise<ProfessorListItem> => {
    const res = await api.post<ProfessorListItem>('/professors/', data);
    return res.data;
  },
  updateProfessor: async (id: number, data: Partial<CreateProfessorInput>): Promise<ProfessorListItem> => {
    const res = await api.patch<ProfessorListItem>(`/professors/${id}/`, data);
    return res.data;
  },
  getUnavailability: async (professorId: number): Promise<ProfessorUnavailability[]> => {
    const res = await api.get<ProfessorUnavailability[]>(`/professors/${professorId}/unavailability/`);
    return res.data;
  },
  addUnavailability: async (professorId: number, data: Partial<ProfessorUnavailability>): Promise<ProfessorUnavailability> => {
    const res = await api.post<ProfessorUnavailability>(`/professors/${professorId}/unavailability/`, data);
    return res.data;
  },
  deleteUnavailability: async (id: number): Promise<void> => {
    await api.delete(`/professor-unavailabilities/${id}/`);
  },
};
