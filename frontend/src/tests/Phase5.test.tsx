import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AutoGenerateModal } from '../components/scheduler/AutoGenerateModal';
import { GenerationProgressModal } from '../components/scheduler/GenerationProgressModal';
import { ProposalPreviewModal } from '../components/scheduler/ProposalPreviewModal';
import { ScoringDashboard } from '../components/scheduler/ScoringDashboard';
import { schedulerService } from '../services/scheduler';
import { Branch, AutoScheduleProposal } from '../types';

vi.mock('../services/scheduler', () => ({
  schedulerService: {
    getTaskStatus: vi.fn(),
    generateTimetable: vi.fn(),
    commitProposal: vi.fn(),
    discardProposal: vi.fn(),
    getProposal: vi.fn(),
    getTimetableScore: vi.fn(),
  },
}));

describe('Phase 5 Frontend Components', () => {
  const mockBranches: Branch[] = [
    {
      id: 1,
      department: 1,
      code: 'BTECH_CSE',
      name: 'B.Tech Computer Science',
      degree_name: 'B.Tech',
      max_semesters: 8,
      is_active: true,
      created_at: '',
      updated_at: '',
    },
    {
      id: 2,
      department: 1,
      code: 'BTECH_ECE',
      name: 'B.Tech Electronics',
      degree_name: 'B.Tech',
      max_semesters: 8,
      is_active: true,
      created_at: '',
      updated_at: '',
    },
  ];

  const mockProposal: AutoScheduleProposal = {
    id: 42,
    schedule_version: 1,
    selected_branches: [1],
    proposed_meetings: [
      {
        teaching_assignment_id: 101,
        course_code: 'CS501',
        course_name: 'Database Management Systems',
        course_type: 'THEORY',
        cohort_id: 10,
        cohort_name: 'CSE Sem 5 Sec A',
        branch_id: 1,
        professor_id: 201,
        professor_name: 'Dr. Sharma',
        room_id: 301,
        room_no: '101',
        building_code: 'ENG',
        room_type: 'CLASSROOM',
        weekday: 1,
        start_slot: 2,
        duration_slots: 1,
      },
      {
        teaching_assignment_id: 102,
        course_code: 'CS502L',
        course_name: 'DBMS Lab',
        course_type: 'LAB',
        cohort_id: 10,
        cohort_name: 'CSE Sem 5 Sec A',
        branch_id: 1,
        professor_id: 201,
        professor_name: 'Dr. Sharma',
        room_id: 302,
        room_no: 'LAB1',
        building_code: 'ENG',
        room_type: 'COMPUTER_LAB',
        weekday: 3,
        start_slot: 1,
        duration_slots: 3,
      },
    ],
    solver_status: 'OPTIMAL',
    quality_score: 93.4,
    unscheduled_offerings: [],
    constraint_score_breakdown: {
      overall_score: 93.4,
      breakdown: {
        student_gaps_score: 95.0,
        professor_gaps_score: 90.0,
        load_balance_score: 92.0,
        consecutive_hours_score: 100.0,
        slot_preference_score: 88.0,
        day_spread_score: 96.0,
      },
      metrics: {
        student_gap_hours: 1,
        professor_gap_hours: 2,
        max_consecutive_hours: 3,
        total_scheduled_meetings: 2,
        total_unscheduled_meetings: 0,
      },
    },
    generation_metadata: {
      solve_time_seconds: 1.45,
      total_tasks: 2,
      placed_meetings: 2,
      unscheduled_meetings: 0,
      replace_existing: true,
      selected_branches: [1],
    },
    status: 'PENDING',
    created_at: '2026-11-05T10:00:00Z',
    updated_at: '2026-11-05T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AutoGenerateModal', () => {
    it('renders branch list and allows selecting branches', () => {
      const handleStart = vi.fn();
      render(
        <AutoGenerateModal
          isOpen={true}
          onClose={() => {}}
          branches={mockBranches}
          onStartGeneration={handleStart}
        />
      );

      expect(screen.getByText('Smart Auto-Scheduling')).toBeDefined();
      expect(screen.getByText('BTECH_CSE')).toBeDefined();
      expect(screen.getByText('BTECH_ECE')).toBeDefined();

      // Submit form
      const submitBtn = screen.getByText('Start Auto-Scheduling');
      fireEvent.click(submitBtn);

      expect(handleStart).toHaveBeenCalledWith({
        branch_ids: [1, 2],
        time_limit: 60,
        replace_existing: true,
      });
    });

    it('shows error if all branches are deselected', () => {
      const handleStart = vi.fn();
      render(
        <AutoGenerateModal
          isOpen={true}
          onClose={() => {}}
          branches={mockBranches}
          onStartGeneration={handleStart}
        />
      );

      // Deselect all
      const deselectBtn = screen.getByText('Deselect All');
      fireEvent.click(deselectBtn);

      // Submit
      const submitBtn = screen.getByText('Start Auto-Scheduling');
      fireEvent.click(submitBtn);

      expect(screen.getByText(/Please select at least one branch/)).toBeDefined();
      expect(handleStart).not.toHaveBeenCalled();
    });
  });

  describe('GenerationProgressModal', () => {
    it('polls status and displays progress', async () => {
      vi.mocked(schedulerService.getTaskStatus).mockResolvedValueOnce({
        task_id: 'task-123',
        status: 'PROGRESS',
        percentage: 45,
        message: 'Solving CP-SAT constraints...',
      });

      render(
        <GenerationProgressModal
          isOpen={true}
          taskId="task-123"
          onComplete={() => {}}
          onCancel={() => {}}
        />
      );

      expect(screen.getByText('Generating Timetable...')).toBeDefined();

      await waitFor(() => {
        expect(screen.getByText('45%')).toBeDefined();
        expect(screen.getByText('Solving CP-SAT constraints...')).toBeDefined();
      });
    });

    it('calls onComplete when task status reaches SUCCESS', async () => {
      const handleComplete = vi.fn();
      vi.mocked(schedulerService.getTaskStatus).mockResolvedValueOnce({
        task_id: 'task-123',
        status: 'SUCCESS',
        percentage: 100,
        message: 'Schedule proposal ready!',
        proposal_id: 42,
      });

      render(
        <GenerationProgressModal
          isOpen={true}
          taskId="task-123"
          onComplete={handleComplete}
          onCancel={() => {}}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Schedule Proposal Ready!')).toBeDefined();
      });

      await waitFor(
        () => {
          expect(handleComplete).toHaveBeenCalledWith(42);
        },
        { timeout: 1500 }
      );
    });
  });

  describe('ProposalPreviewModal', () => {
    it('renders proposed timetable grid, quality score, and meetings', () => {
      render(
        <ProposalPreviewModal
          isOpen={true}
          proposal={mockProposal}
          onClose={() => {}}
          onCommit={() => {}}
          onDiscard={() => {}}
        />
      );

      expect(screen.getByText('Auto-Schedule Proposal Preview')).toBeDefined();
      expect(screen.getByText('Proposal #42')).toBeDefined();
      expect(screen.getByText('OPTIMAL')).toBeDefined();
      expect(screen.getByText(/93.4 \/ 100/)).toBeDefined();
      expect(screen.getByText('CS501')).toBeDefined();
      expect(screen.getAllByText('CS502L').length).toBeGreaterThan(0);
    });

    it('triggers commit callback when user confirms commit', async () => {
      const handleCommit = vi.fn();
      render(
        <ProposalPreviewModal
          isOpen={true}
          proposal={mockProposal}
          onClose={() => {}}
          onCommit={handleCommit}
          onDiscard={() => {}}
        />
      );

      const commitBtn = screen.getByText('Commit Proposal to Live Timetable');
      fireEvent.click(commitBtn);

      // Confirm prompt dialog appears
      expect(screen.getByText('Confirm Timetable Commit')).toBeDefined();
      const confirmBtn = screen.getByText('Confirm & Commit');
      fireEvent.click(confirmBtn);

      expect(handleCommit).toHaveBeenCalledWith(42);
    });

    it('triggers discard callback', () => {
      const handleDiscard = vi.fn();
      render(
        <ProposalPreviewModal
          isOpen={true}
          proposal={mockProposal}
          onClose={() => {}}
          onCommit={() => {}}
          onDiscard={handleDiscard}
        />
      );

      const discardBtn = screen.getByText('Discard Proposal');
      fireEvent.click(discardBtn);

      expect(handleDiscard).toHaveBeenCalledWith(42);
    });
  });

  describe('ScoringDashboard', () => {
    it('renders soft constraint breakdown and metrics', () => {
      render(
        <ScoringDashboard
          overallScore={93.4}
          breakdown={mockProposal.constraint_score_breakdown.breakdown}
          metrics={mockProposal.constraint_score_breakdown.metrics}
        />
      );

      expect(screen.getByText('93.4')).toBeDefined();
      expect(screen.getByText('Student Timetable Gaps')).toBeDefined();
      expect(screen.getByText('Professor Timetable Gaps')).toBeDefined();
      expect(screen.getByText('Weekday Load Balance')).toBeDefined();
      expect(screen.getByText('Consecutive Hours Limit')).toBeDefined();
    });
  });
});
