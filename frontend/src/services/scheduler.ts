import { api } from './api';
import {
  GenerateTimetableInput,
  TaskStatusResponse,
  AutoScheduleProposal,
  ScheduleScoreReport,
  CommitProposalResponse,
} from '../types';

export const schedulerService = {
  // Generate Timetable background task
  generateTimetable: async (
    versionId: number,
    data: GenerateTimetableInput
  ): Promise<{ task_id: string; status: string; version_id: number; message: string }> => {
    const res = await api.post(`/timetable/${versionId}/generate`, data);
    return res.data;
  },

  // Poll Task Status
  getTaskStatus: async (taskId: string): Promise<TaskStatusResponse> => {
    const res = await api.get<TaskStatusResponse>(`/tasks/${taskId}/status`);
    return res.data;
  },

  // List Proposals for Version
  getProposals: async (
    versionId: number,
    status?: string
  ): Promise<AutoScheduleProposal[]> => {
    const params = status ? { status } : {};
    const res = await api.get<{ results: AutoScheduleProposal[] } | AutoScheduleProposal[]>(
      `/timetable/${versionId}/proposals`,
      { params }
    );
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },

  // Retrieve single proposal
  getProposal: async (
    versionId: number,
    proposalId: number
  ): Promise<AutoScheduleProposal> => {
    const res = await api.get<AutoScheduleProposal>(
      `/timetable/${versionId}/proposals/${proposalId}`
    );
    return res.data;
  },

  // Commit Proposal
  commitProposal: async (
    versionId: number,
    proposalId: number
  ): Promise<CommitProposalResponse> => {
    const res = await api.post<CommitProposalResponse>(
      `/timetable/${versionId}/commit-proposal`,
      { proposal_id: proposalId }
    );
    return res.data;
  },

  // Discard Proposal
  discardProposal: async (
    versionId: number,
    proposalId: number
  ): Promise<{ status: string; proposal_id: number; message: string }> => {
    const res = await api.post(`/timetable/${versionId}/discard-proposal`, {
      proposal_id: proposalId,
    });
    return res.data;
  },

  // Quality Score Report
  getTimetableScore: async (versionId: number): Promise<ScheduleScoreReport> => {
    const res = await api.get<ScheduleScoreReport>(`/timetable/${versionId}/score`);
    return res.data;
  },
};

