import { api } from './api';
import {
  Department,
  Branch,
  AcademicYear,
  AcademicTerm,
  TimeSlot,
  Cohort,
  InstructionGroup,
  Course,
  CurriculumItem,
  CourseOffering,
  TeachingAssignment,
} from '../types';

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
    return Array.isArray(response.data) ? response.data : response.data.results || [];
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
    const params = departmentId ? { department: departmentId } : {};
    const response = await api.get<{ results?: Branch[] } | Branch[]>('/branches/', { params });
    return Array.isArray(response.data) ? response.data : response.data.results || [];
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

  // Academic Years
  async getAcademicYears(): Promise<AcademicYear[]> {
    const res = await api.get<{ results: AcademicYear[] } | AcademicYear[]>('/academic-years/');
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  async createAcademicYear(data: Partial<AcademicYear>): Promise<AcademicYear> {
    const res = await api.post<AcademicYear>('/academic-years/', data);
    return res.data;
  },
  async updateAcademicYear(id: number, data: Partial<AcademicYear>): Promise<AcademicYear> {
    const res = await api.patch<AcademicYear>(`/academic-years/${id}/`, data);
    return res.data;
  },
  async deleteAcademicYear(id: number): Promise<void> {
    await api.delete(`/academic-years/${id}/`);
  },

  // Academic Terms
  async getAcademicTerms(yearId?: number): Promise<AcademicTerm[]> {
    const params = yearId ? { academic_year: yearId } : {};
    const res = await api.get<{ results: AcademicTerm[] } | AcademicTerm[]>('/academic-terms/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  async createAcademicTerm(data: Partial<AcademicTerm>): Promise<AcademicTerm> {
    const res = await api.post<AcademicTerm>('/academic-terms/', data);
    return res.data;
  },
  async updateAcademicTerm(id: number, data: Partial<AcademicTerm>): Promise<AcademicTerm> {
    const res = await api.patch<AcademicTerm>(`/academic-terms/${id}/`, data);
    return res.data;
  },
  async deleteAcademicTerm(id: number): Promise<void> {
    await api.delete(`/academic-terms/${id}/`);
  },

  // Time Slots
  async getTimeSlots(): Promise<TimeSlot[]> {
    const res = await api.get<TimeSlot[]>('/time-slots/');
    return Array.isArray(res.data) ? res.data : [];
  },

  // Cohorts
  async getCohorts(params?: { branch?: number; term?: number; semester?: number }): Promise<Cohort[]> {
    const res = await api.get<{ results: Cohort[] } | Cohort[]>('/cohorts/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  async createCohort(data: Partial<Cohort>): Promise<Cohort> {
    const res = await api.post<Cohort>('/cohorts/', data);
    return res.data;
  },
  async updateCohort(id: number, data: Partial<Cohort>): Promise<Cohort> {
    const res = await api.patch<Cohort>(`/cohorts/${id}/`, data);
    return res.data;
  },
  async deleteCohort(id: number): Promise<void> {
    await api.delete(`/cohorts/${id}/`);
  },
  async generateGroups(cohortId: number, type: 'SPLIT' | 'SINGLE'): Promise<InstructionGroup[]> {
    const res = await api.post<InstructionGroup[]>(`/cohorts/${cohortId}/generate-groups/`, { type });
    return res.data;
  },

  // Instruction Groups
  async createInstructionGroup(data: Partial<InstructionGroup>): Promise<InstructionGroup> {
    const res = await api.post<InstructionGroup>('/instruction-groups/', data);
    return res.data;
  },
  async deleteInstructionGroup(id: number): Promise<void> {
    await api.delete(`/instruction-groups/${id}/`);
  },

  // Courses
  async getCourses(params?: { course_type?: string; department?: number }): Promise<Course[]> {
    const res = await api.get<{ results: Course[] } | Course[]>('/courses/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  async createCourse(data: Partial<Course>): Promise<Course> {
    const res = await api.post<Course>('/courses/', data);
    return res.data;
  },
  async updateCourse(id: number, data: Partial<Course>): Promise<Course> {
    const res = await api.patch<Course>(`/courses/${id}/`, data);
    return res.data;
  },
  async deleteCourse(id: number): Promise<void> {
    await api.delete(`/courses/${id}/`);
  },

  // Curriculum Items
  async getCurriculumItems(params?: { branch?: number; semester?: number }): Promise<CurriculumItem[]> {
    const res = await api.get<{ results: CurriculumItem[] } | CurriculumItem[]>('/curriculum/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  async createCurriculumItem(data: Partial<CurriculumItem>): Promise<CurriculumItem> {
    const res = await api.post<CurriculumItem>('/curriculum/', data);
    return res.data;
  },
  async deleteCurriculumItem(id: number): Promise<void> {
    await api.delete(`/curriculum/${id}/`);
  },

  // Course Offerings
  async getCourseOfferings(params?: { term?: number; cohort?: number; branch?: number }): Promise<CourseOffering[]> {
    const res = await api.get<{ results: CourseOffering[] } | CourseOffering[]>('/course-offerings/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  async populateFromCurriculum(cohortId: number): Promise<CourseOffering[]> {
    const res = await api.post<CourseOffering[]>('/course-offerings/populate-from-curriculum/', { cohort_id: cohortId });
    return res.data;
  },

  // Teaching Assignments
  async getTeachingAssignments(params?: { offering?: number; professor?: number; cohort?: number; term?: number }): Promise<TeachingAssignment[]> {
    const res = await api.get<{ results: TeachingAssignment[] } | TeachingAssignment[]>('/teaching-assignments/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  async createTeachingAssignment(data: Partial<TeachingAssignment>): Promise<TeachingAssignment> {
    const res = await api.post<TeachingAssignment>('/teaching-assignments/', data);
    return res.data;
  },
  async deleteTeachingAssignment(id: number): Promise<void> {
    await api.delete(`/teaching-assignments/${id}/`);
  },
};
