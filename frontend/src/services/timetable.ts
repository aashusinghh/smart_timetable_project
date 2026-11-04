import { api } from './api';
import {
  ScheduleVersion,
  ScheduledMeeting,
  TimetableGridResponse,
  ValidatePlacementInput,
  ValidationResponse,
  SaveMeetingInput,
  AvailableRoomItem,
  HolidayCalendar,
  DateOverride,
  AuditLogEntry,
  MyTimetableResponse,
  BranchTimetableResponse,
  ValidationSweepResponse,
} from '../types';

export const timetableService = {
  // Versions
  getVersions: async (termId?: number): Promise<ScheduleVersion[]> => {
    const params = termId ? { term: termId } : {};
    const res = await api.get<{ results: ScheduleVersion[] } | ScheduleVersion[]>('/timetable/versions/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },

  createVersion: async (data: Partial<ScheduleVersion>): Promise<ScheduleVersion> => {
    const res = await api.post<ScheduleVersion>('/timetable/versions/', data);
    return res.data;
  },

  submitReview: async (versionId: number): Promise<ScheduleVersion> => {
    const res = await api.post<ScheduleVersion>(`/timetable/versions/${versionId}/submit-review/`);
    return res.data;
  },

  sendBackToDraft: async (versionId: number, reason?: string): Promise<ScheduleVersion> => {
    const res = await api.post<ScheduleVersion>(`/timetable/versions/${versionId}/send-back/`, { reason });
    return res.data;
  },

  publishSchedule: async (versionId: number): Promise<ScheduleVersion> => {
    const res = await api.post<ScheduleVersion>(`/timetable/versions/${versionId}/publish/`);
    return res.data;
  },

  validateSweep: async (versionId: number): Promise<ValidationSweepResponse> => {
    const res = await api.get<ValidationSweepResponse>(`/timetable/versions/${versionId}/validate-sweep/`);
    return res.data;
  },

  // Grid
  getGrid: async (
    versionId: number,
    params?: { cohort_id?: number; branch_id?: number; professor_id?: number; room_id?: number }
  ): Promise<TimetableGridResponse> => {
    const res = await api.get<TimetableGridResponse>(`/timetable/${versionId}/grid`, { params });
    return res.data;
  },

  // Authoritative Validation
  validatePlacement: async (data: ValidatePlacementInput): Promise<ValidationResponse> => {
    const res = await api.post<ValidationResponse>('/timetable/validate', data);
    return res.data;
  },

  // Meetings CRUD
  saveMeeting: async (data: SaveMeetingInput): Promise<ScheduledMeeting> => {
    const res = await api.post<ScheduledMeeting>('/timetable/meetings/', data);
    return res.data;
  },

  updateMeeting: async (id: number, data: Partial<SaveMeetingInput>): Promise<ScheduledMeeting> => {
    const res = await api.patch<ScheduledMeeting>(`/timetable/meetings/${id}/`, data);
    return res.data;
  },

  deleteMeeting: async (id: number): Promise<void> => {
    await api.delete(`/timetable/meetings/${id}/`);
  },

  // Available Rooms Query
  getAvailableRooms: async (
    versionId: number,
    params: { weekday: number; start_slot: number; duration_slots: number; room_type?: string; min_capacity?: number }
  ): Promise<AvailableRoomItem[]> => {
    const res = await api.get<AvailableRoomItem[]>(`/timetable/${versionId}/available-rooms`, { params });
    return res.data;
  },

  // Batch updates
  batchUpdate: async (versionId: number, updates: any[]): Promise<ScheduledMeeting[]> => {
    const res = await api.post<ScheduledMeeting[]>('/timetable/batch-update', {
      schedule_version_id: versionId,
      updates,
    });
    return res.data;
  },

  // Phase 4: Read-Only Timetable Endpoints
  getMyTimetable: async (termId?: number): Promise<MyTimetableResponse> => {
    const params = termId ? { term_id: termId } : {};
    const res = await api.get<MyTimetableResponse>('/my-timetable/', { params });
    return res.data;
  },

  getProfessorTimetable: async (
    profId: number,
    termId?: number
  ): Promise<{ professor_id: number; professor_name: string; meetings: ScheduledMeeting[] }> => {
    const params = termId ? { term_id: termId } : {};
    const res = await api.get<{ professor_id: number; professor_name: string; meetings: ScheduledMeeting[] }>(
      `/professors/${profId}/timetable/`,
      { params }
    );
    return res.data;
  },

  getBranchTimetable: async (
    branchId: number,
    params?: { term_id?: number; cohort_id?: number; semester_no?: number }
  ): Promise<BranchTimetableResponse> => {
    const res = await api.get<BranchTimetableResponse>(`/branches/${branchId}/timetable/`, { params });
    return res.data;
  },

  // Holidays
  getHolidays: async (termId?: number): Promise<HolidayCalendar[]> => {
    const params = termId ? { term: termId } : {};
    const res = await api.get<{ results: HolidayCalendar[] } | HolidayCalendar[]>('/holidays/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },

  createHoliday: async (data: Partial<HolidayCalendar>): Promise<HolidayCalendar> => {
    const res = await api.post<HolidayCalendar>('/holidays/', data);
    return res.data;
  },

  deleteHoliday: async (id: number): Promise<void> => {
    await api.delete(`/holidays/${id}/`);
  },

  // Date Overrides
  getDateOverrides: async (params?: { meeting?: number; status?: string }): Promise<DateOverride[]> => {
    const res = await api.get<{ results: DateOverride[] } | DateOverride[]>('/date-overrides/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },

  createDateOverride: async (data: Partial<DateOverride>): Promise<DateOverride> => {
    const res = await api.post<DateOverride>('/date-overrides/', data);
    return res.data;
  },

  deleteDateOverride: async (id: number): Promise<void> => {
    await api.delete(`/date-overrides/${id}/`);
  },

  // Audit Logs
  getAuditLogs: async (params?: {
    version?: number;
    meeting_id?: number;
    user_id?: number;
    action?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
  }): Promise<{ results: AuditLogEntry[]; count: number }> => {
    const res = await api.get<{ results: AuditLogEntry[]; count: number } | AuditLogEntry[]>('/audit-logs/', { params });
    if (Array.isArray(res.data)) {
      return { results: res.data, count: res.data.length };
    }
    return res.data;
  },
};
