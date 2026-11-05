import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calendar,
  Clock,
  Plus,
  Trash2,
  X,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  DoorOpen,
  UserCheck,
  Coffee,
  Sun,
  Sunset,
  ChevronRight,
  Filter,
  RefreshCw,
  Edit2,
  HelpCircle,
  FileCode2,
  Wifi,
  WifiOff,
  ShieldCheck,
  Award,
  BarChart3,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTimetableSocket } from '../hooks/useTimetableSocket';
import { timetableService } from '../services/timetable';
import { academicsService } from '../services/academics';
import { facilitiesService } from '../services/facilities';
import { schedulerService } from '../services/scheduler';
import { AutoGenerateModal } from '../components/scheduler/AutoGenerateModal';
import { GenerationProgressModal } from '../components/scheduler/GenerationProgressModal';
import { ProposalPreviewModal } from '../components/scheduler/ProposalPreviewModal';
import {
  ScheduleVersion,
  ScheduledMeeting,
  ValidationResponse,
  ConflictDetail,
  AvailableRoomItem,
  CourseOffering,
  TeachingAssignment,
  Cohort,
  Branch,
  AcademicTerm,
  Room,
  AutoScheduleProposal,
} from '../types';

const WEEKDAYS = [
  { id: 1, name: 'Monday', short: 'Mon' },
  { id: 2, name: 'Tuesday', short: 'Tue' },
  { id: 3, name: 'Wednesday', short: 'Wed' },
  { id: 4, name: 'Thursday', short: 'Thu' },
  { id: 5, name: 'Friday', short: 'Fri' },
];

const SLOTS = [
  { no: 1, time: '08:30 - 09:30', session: 'MORNING' },
  { no: 2, time: '09:30 - 10:30', session: 'MORNING' },
  { no: 3, time: '10:30 - 11:30', session: 'MORNING' },
  { no: 4, time: '11:30 - 12:30', session: 'MORNING' },
  // Lunch between 4 and 5
  { no: 5, time: '14:00 - 15:00', session: 'AFTERNOON' },
  { no: 6, time: '15:00 - 16:00', session: 'AFTERNOON' },
  { no: 7, time: '16:00 - 17:00', session: 'AFTERNOON' },
  { no: 8, time: '17:00 - 18:00', session: 'AFTERNOON' },
];

export const TimetablePlannerPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Selection states
  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();
  const [selectedVersionId, setSelectedVersionId] = useState<number | undefined>();
  const [selectedCohortId, setSelectedCohortId] = useState<number | undefined>();

  // Dragging / Active placement state
  const [activeOffering, setActiveOffering] = useState<CourseOffering | null>(null);
  const [activeAssignment, setActiveAssignment] = useState<TeachingAssignment | null>(null);
  const [selectedRoomId, setSelectedRoomId] = useState<number | undefined>();

  // Hover / slot validation state
  const [hoveredSlot, setHoveredSlot] = useState<{ weekday: number; slot_no: number } | null>(null);
  const [slotValidation, setSlotValidation] = useState<ValidationResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Modal / Detail state
  const [selectedMeeting, setSelectedMeeting] = useState<ScheduledMeeting | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isCreateVersionOpen, setIsCreateVersionOpen] = useState(false);
  const [newVersionName, setNewVersionName] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Phase 5 Auto-Scheduler State
  const [isAutoGenerateModalOpen, setIsAutoGenerateModalOpen] = useState(false);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<AutoScheduleProposal | null>(null);
  const [isCommittingProposal, setIsCommittingProposal] = useState(false);
  const [isDiscardingProposal, setIsDiscardingProposal] = useState(false);

  // Queries
  const { data: terms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const activeTerm = terms.find((t) => t.id === selectedTermId) || terms[0];

  const { data: versions = [] } = useQuery({
    queryKey: ['timetable-versions', activeTerm?.id],
    queryFn: () => timetableService.getVersions(activeTerm?.id),
    enabled: !!activeTerm,
  });

  const activeVersion = versions.find((v) => v.id === selectedVersionId) || versions[0];

  const { data: cohorts = [] } = useQuery({
    queryKey: ['cohorts', activeTerm?.id],
    queryFn: () => academicsService.getCohorts({ term: activeTerm?.id }),
    enabled: !!activeTerm,
  });

  const activeCohort = cohorts.find((c) => c.id === selectedCohortId) || cohorts[0];

  // Grid Query
  const { data: gridData, refetch: refetchGrid } = useQuery({
    queryKey: ['timetable-grid', activeVersion?.id, activeCohort?.id],
    queryFn: () =>
      activeVersion
        ? timetableService.getGrid(activeVersion.id, { cohort_id: activeCohort?.id })
        : Promise.resolve({ schedule_version_id: 0, revision: 1, status: 'DRAFT' as const, meetings: [], total_count: 0 }),
    enabled: !!activeVersion,
  });

  // Course Offerings & Assignments for cohort
  const { data: offerings = [] } = useQuery({
    queryKey: ['course-offerings', activeCohort?.id],
    queryFn: () => academicsService.getCourseOfferings({ cohort: activeCohort?.id }),
    enabled: !!activeCohort,
  });

  const { data: assignments = [] } = useQuery({
    queryKey: ['teaching-assignments', activeCohort?.id],
    queryFn: () => academicsService.getTeachingAssignments({ cohort: activeCohort?.id }),
    enabled: !!activeCohort,
  });

  // Rooms query
  const { data: rooms = [] } = useQuery({
    queryKey: ['rooms'],
    queryFn: () => facilitiesService.getRooms(),
  });

  // Branches query (for auto-scheduling branch picker)
  const { data: branches = [] } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  // Schedule Quality Score query
  const { data: qualityScoreData, refetch: refetchScore } = useQuery({
    queryKey: ['timetable-score', activeVersion?.id],
    queryFn: () => (activeVersion ? schedulerService.getTimetableScore(activeVersion.id) : null),
    enabled: !!activeVersion,
  });

  // Mutations
  const createVersionMutation = useMutation({
    mutationFn: (data: Partial<ScheduleVersion>) => timetableService.createVersion(data),
    onSuccess: (newVer) => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSelectedVersionId(newVer.id);
      setIsCreateVersionOpen(false);
      setNewVersionName('');
    },
  });

  const saveMeetingMutation = useMutation({
    mutationFn: (data: any) => timetableService.saveMeeting(data),
    onSuccess: () => {
      refetchGrid();
      setActiveOffering(null);
      setActiveAssignment(null);
      setHoveredSlot(null);
      setSlotValidation(null);
      setSuccessToast('Meeting placed and reservations locked successfully!');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.conflicts?.[0]?.message ||
        'Conflict detected! Unable to place meeting.';
      setErrorMessage(msg);
    },
  });

  const deleteMeetingMutation = useMutation({
    mutationFn: (id: number) => timetableService.deleteMeeting(id),
    onSuccess: () => {
      refetchGrid();
      setIsDetailModalOpen(false);
      setSelectedMeeting(null);
      setSuccessToast('Meeting removed and reservations released.');
      setTimeout(() => setSuccessToast(null), 3000);
    },
  });

  const updateMeetingMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => timetableService.updateMeeting(id, data),
    onSuccess: () => {
      refetchGrid();
      setIsDetailModalOpen(false);
      setSelectedMeeting(null);
      setSuccessToast('Meeting updated successfully!');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || 'Failed to update meeting.';
      setErrorMessage(msg);
    },
  });

  const { user } = useAuth();
  const isSuperAdmin = user?.is_superuser || user?.roles?.includes('SUPER_ADMIN');
  const isLocked = activeVersion?.status === 'PUBLISHED' || (activeVersion?.status === 'UNDER_REVIEW' && !isSuperAdmin);

  // WebSocket Live Updates
  const { isConnected } = useTimetableSocket(activeVersion?.id, {
    onEvent: (event) => {
      if (event.type === 'schedule.published') {
        setSuccessToast(`📢 Schedule has been officially PUBLISHED!`);
        setTimeout(() => setSuccessToast(null), 5000);
      }
    },
  });

  const submitReviewMutation = useMutation({
    mutationFn: (id: number) => timetableService.submitReview(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast('Schedule version submitted for administrative review!');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to submit for review.');
    },
  });

  const sendBackMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => timetableService.sendBackToDraft(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast('Schedule returned to draft status.');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || 'Failed to send back.');
    },
  });

  const publishMutation = useMutation({
    mutationFn: (id: number) => timetableService.publishSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast('🎉 Timetable officially PUBLISHED! Clashes resolved.');
      setTimeout(() => setSuccessToast(null), 4000);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || 'Validation clashes detected during pre-publication sweep.';
      setErrorMessage(msg);
    },
  });

  const isAuthorizedToAutoSchedule = isSuperAdmin || user?.roles?.includes('BRANCH_COORDINATOR');

  // Auto-Scheduling Handlers
  const handleStartGeneration = async (config: {
    branch_ids: number[];
    time_limit: number;
    replace_existing: boolean;
  }) => {
    if (!activeVersion) return;
    try {
      const res = await schedulerService.generateTimetable(activeVersion.id, config);
      setActiveTaskId(res.task_id);
      setIsAutoGenerateModalOpen(false);
      setIsProgressModalOpen(true);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to start auto-scheduling.';
      setErrorMessage(msg);
    }
  };

  const handleGenerationComplete = async (proposalId: number) => {
    if (!activeVersion) return;
    setIsProgressModalOpen(false);
    try {
      const prop = await schedulerService.getProposal(activeVersion.id, proposalId);
      setSelectedProposal(prop);
      setIsPreviewModalOpen(true);
    } catch (err: any) {
      setErrorMessage('Failed to load generated proposal preview.');
    }
  };

  const handleCommitProposal = async (proposalId: number) => {
    if (!activeVersion) return;
    setIsCommittingProposal(true);
    try {
      const res = await schedulerService.commitProposal(activeVersion.id, proposalId);
      setIsPreviewModalOpen(false);
      setSelectedProposal(null);
      refetchGrid();
      refetchScore();
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast(`🎉 ${res.message || 'Proposal committed successfully!'}`);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.conflicts?.[0]?.message ||
        'Failed to commit proposal. A conflict may have occurred.';
      setErrorMessage(msg);
    } finally {
      setIsCommittingProposal(false);
    }
  };

  const handleDiscardProposal = async (proposalId: number) => {
    if (!activeVersion) return;
    setIsDiscardingProposal(true);
    try {
      await schedulerService.discardProposal(activeVersion.id, proposalId);
      setIsPreviewModalOpen(false);
      setSelectedProposal(null);
      setSuccessToast('Proposal discarded successfully.');
      setTimeout(() => setSuccessToast(null), 3000);
    } catch (err: any) {
      setErrorMessage('Failed to discard proposal.');
    } finally {
      setIsDiscardingProposal(false);
    }
  };

  // Set default selections
  useEffect(() => {
    if (terms.length > 0 && !selectedTermId) {
      setSelectedTermId(terms[0].id);
    }
  }, [terms, selectedTermId]);

  useEffect(() => {
    if (versions.length > 0 && !selectedVersionId) {
      setSelectedVersionId(versions[0].id);
    }
  }, [versions, selectedVersionId]);

  useEffect(() => {
    if (cohorts.length > 0 && !selectedCohortId) {
      setSelectedCohortId(cohorts[0].id);
    }
  }, [cohorts, selectedCohortId]);

  // Set default room
  useEffect(() => {
    if (rooms.length > 0 && !selectedRoomId) {
      setSelectedRoomId(rooms[0].id);
    }
  }, [rooms, selectedRoomId]);

  // Meetings map: (weekday, slot_no) -> ScheduledMeeting
  const meetingsBySlot = useMemo(() => {
    const map = new Map<string, ScheduledMeeting>();
    if (!gridData?.meetings) return map;
    gridData.meetings.forEach((m) => {
      for (let s = m.start_slot; s <= m.end_slot; s++) {
        map.set(`${m.weekday}-${s}`, m);
      }
    });
    return map;
  }, [gridData]);

  // Calculate meeting counts per offering
  const scheduledCountByOffering = useMemo(() => {
    const counts: Record<number, number> = {};
    if (!gridData?.meetings) return counts;
    gridData.meetings.forEach((m) => {
      const asgn = assignments.find((a) => a.id === m.teaching_assignment);
      if (asgn) {
        counts[asgn.course_offering] = (counts[asgn.course_offering] || 0) + 1;
      }
    });
    return counts;
  }, [gridData, assignments]);

  // Debounced slot hover validation
  const validateSlotHover = async (weekday: number, slot_no: number) => {
    if (!activeAssignment || !activeVersion || !selectedRoomId) return;
    setIsValidating(true);
    setHoveredSlot({ weekday, slot_no });

    const isLab = activeOffering?.course_type === 'LAB';
    const duration = isLab ? 3 : 1;

    try {
      const result = await timetableService.validatePlacement({
        schedule_version_id: activeVersion.id,
        teaching_assignment_id: activeAssignment.id,
        weekday,
        start_slot: slot_no,
        duration_slots: duration,
        room_id: selectedRoomId,
      });
      setSlotValidation(result);
    } catch {
      setSlotValidation({ allowed: false, conflicts: [{ type: 'API_ERROR', message: 'Validation request failed' }] });
    } finally {
      setIsValidating(false);
    }
  };

  const handleSlotClick = (weekday: number, slot_no: number) => {
    // If a meeting is already in that cell, open details
    const existing = meetingsBySlot.get(`${weekday}-${slot_no}`);
    if (existing) {
      setSelectedMeeting(existing);
      setIsDetailModalOpen(true);
      return;
    }

    if (isLocked) {
      setErrorMessage(`Schedule version is currently ${activeVersion?.status}. Modifications are locked.`);
      return;
    }

    // If an offering is active, place it!
    if (activeAssignment && activeVersion && selectedRoomId) {
      setErrorMessage(null);
      const isLab = activeOffering?.course_type === 'LAB';
      const duration = isLab ? 3 : 1;

      saveMeetingMutation.mutate({
        schedule_version_id: activeVersion.id,
        teaching_assignment_id: activeAssignment.id,
        weekday,
        start_slot: slot_no,
        duration_slots: duration,
        room_id: selectedRoomId,
      });
    }
  };

  const selectOfferingForPlacement = (offering: CourseOffering) => {
    const asgn = assignments.find((a) => a.course_offering === offering.id);
    if (!asgn) {
      alert(`No professor assigned to ${offering.course_code} yet! Please assign a faculty member first.`);
      return;
    }
    setActiveOffering(offering);
    setActiveAssignment(asgn);

    // Pick compatible room type automatically
    if (offering.course_type === 'LAB') {
      const labRoom = rooms.find((r) => r.room_type === 'COMPUTER_LAB' || r.room_type === 'ELECTRONICS_LAB');
      if (labRoom) setSelectedRoomId(labRoom.id);
    } else {
      const classRoom = rooms.find((r) => r.room_type === 'CLASSROOM');
      if (classRoom) setSelectedRoomId(classRoom.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {successToast && (
        <div className="fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-semibold shadow-lg animate-bounce">
          <CheckCircle2 className="w-4 h-4" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Top Header & Selector Chain */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>Phase 5 — Smart Auto-Scheduling with OR-Tools CP-SAT</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Timetable Planner</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Drag or click courses into weekly time slots or use AI auto-scheduling with Google OR-Tools optimization.
          </p>
        </div>

        {/* Action Controls & Live Sync */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Quality Score Badge */}
          {qualityScoreData && (
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800 shadow-xs"
              title="Schedule Quality Score"
            >
              <Award className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Score: {qualityScoreData.overall_score.toFixed(1)}/100</span>
            </div>
          )}

          {/* WebSocket Status Indicator */}
          {isConnected ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Live Sync</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
              <span className="w-2 h-2 rounded-full bg-slate-400"></span>
              <span>Connecting...</span>
            </div>
          )}

          {/* Phase 5 Auto-Generate Button */}
          {isAuthorizedToAutoSchedule && activeVersion?.status === 'DRAFT' && (
            <button
              onClick={() => setIsAutoGenerateModalOpen(true)}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-primary-600 via-indigo-600 to-primary-700 hover:from-primary-700 hover:to-indigo-700 text-white shadow-md shadow-primary-500/25 transition-all flex items-center gap-1.5"
              title="Smart automatic timetable generator with Google OR-Tools"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Auto-Generate</span>
            </button>
          )}

          {/* Workflow Action Buttons */}
          {activeVersion?.status === 'DRAFT' && (
            <button
              onClick={() => {
                if (confirm(`Submit ${activeVersion.name || 'Draft'} for Administrative Review?`)) {
                  submitReviewMutation.mutate(activeVersion.id);
                }
              }}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-700 text-white shadow-sm transition-colors flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Submit for Review</span>
            </button>
          )}

          {activeVersion?.status === 'UNDER_REVIEW' && isSuperAdmin && (
            <>
              <button
                onClick={() => {
                  const reason = prompt('Reason for returning schedule to draft:');
                  if (reason !== null) {
                    sendBackMutation.mutate({ id: activeVersion.id, reason });
                  }
                }}
                className="px-3 py-2 text-xs font-semibold rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-900 transition-colors"
              >
                Send Back to Draft
              </button>
              <button
                onClick={() => {
                  if (confirm(`Run clash verification and PUBLISH ${activeVersion.name}?`)) {
                    publishMutation.mutate(activeVersion.id);
                  }
                }}
                className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-colors flex items-center gap-1.5"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Approve & Publish</span>
              </button>
            </>
          )}

          {activeVersion?.status === 'PUBLISHED' && (
            <span className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>PUBLISHED (Locked)</span>
            </span>
          )}

          <button
            onClick={() => setIsCreateVersionOpen(true)}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100 transition-colors"
          >
            + New Draft Version
          </button>
        </div>
      </div>

      {/* Lock Notice Banner */}
      {isLocked && (
        <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs font-semibold text-amber-800 dark:text-amber-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            {activeVersion?.status === 'PUBLISHED'
              ? 'This timetable is officially PUBLISHED. Changes are locked. To make adjustments, create a new draft version.'
              : 'This timetable is currently UNDER_REVIEW by administration. Coordinators cannot edit meetings during review.'}
          </span>
        </div>
      )}

      {/* Selector Chain Bar (Branch -> Term -> Cohort -> Version) */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center gap-4">
        {/* Term */}
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Academic Term</label>
          <select
            value={activeTerm?.id || ''}
            onChange={(e) => setSelectedTermId(Number(e.target.value))}
            className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-medium"
          >
            {terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {/* Schedule Version */}
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Schedule Version</label>
          <div className="flex items-center gap-2">
            <select
              value={activeVersion?.id || ''}
              onChange={(e) => setSelectedVersionId(Number(e.target.value))}
              className="px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-bold"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name || `Version ${v.version_no}`} ({v.status}) • Rev {v.revision}
                </option>
              ))}
            </select>
            {activeVersion && (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                {activeVersion.status}
              </span>
            )}
          </div>
        </div>

        {/* Cohort Selector */}
        <div className="min-w-[240px]">
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Cohort (Section)</label>
          <select
            value={activeCohort?.id || ''}
            onChange={(e) => setSelectedCohortId(Number(e.target.value))}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-medium"
          >
            {cohorts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.branch_code} Sem {c.semester_no} Sec {c.section_code} ({c.student_count} students)
              </option>
            ))}
          </select>
        </div>

        {/* Room Selector for Placement */}
        {activeOffering && (
          <div className="ml-auto flex items-center gap-2 p-2 rounded-lg bg-primary-50 dark:bg-primary-950/40 border border-primary-200 dark:border-primary-800">
            <DoorOpen className="w-4 h-4 text-primary-600" />
            <div>
              <label className="block text-[10px] font-bold text-primary-800 dark:text-primary-300">
                Target Room for Placement:
              </label>
              <select
                value={selectedRoomId || ''}
                onChange={(e) => setSelectedRoomId(Number(e.target.value))}
                className="px-2 py-1 text-xs rounded border border-primary-300 bg-white dark:bg-slate-800"
              >
                {rooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.room_no} ({r.building_code}) - {r.room_type_display} [Cap {r.capacity}]
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Error / Conflict Alert Banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start justify-between gap-3 text-xs text-rose-800 dark:text-rose-200">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Layout: Left Offerings Palette + Right Weekly Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Left Col: Unscheduled Course Offerings Palette */}
        <div className="xl:col-span-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">Course Offerings</h2>
              <p className="text-[11px] text-slate-500">
                Click a course to begin placement on the timetable grid.
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-slate-400">{offerings.length} courses</span>
          </div>

          {activeOffering && (
            <div className="p-3 rounded-xl bg-primary-50 dark:bg-primary-950/50 border border-primary-200 dark:border-primary-800 text-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-primary-900 dark:text-primary-200">Placing Active Course:</span>
                <button
                  onClick={() => {
                    setActiveOffering(null);
                    setActiveAssignment(null);
                  }}
                  className="text-primary-500 hover:text-primary-700 font-bold"
                >
                  Cancel
                </button>
              </div>
              <p className="font-mono font-semibold">{activeOffering.course_code} — {activeOffering.course_name}</p>
              <p className="text-[11px] text-slate-500">
                Pattern: {activeOffering.course_type === 'LAB' ? '2 × 3h Continuous Lab' : `${activeOffering.course_credit} × 1h Theory`}
              </p>
            </div>
          )}

          <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
            {offerings.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-6">
                No offerings found for this cohort. Populate courses in the Teaching Assignments screen.
              </p>
            ) : (
              offerings.map((offering) => {
                const asgn = assignments.find((a) => a.course_offering === offering.id);
                const isSelected = activeOffering?.id === offering.id;
                const isLab = offering.course_type === 'LAB';
                const scheduledCount = scheduledCountByOffering[offering.id] || 0;
                const maxMeetings = isLab ? 2 : (offering.course_credit || 3);
                const isComplete = scheduledCount >= maxMeetings;

                return (
                  <div
                    key={offering.id}
                    onClick={() => selectOfferingForPlacement(offering)}
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50/40 dark:bg-primary-950/30 shadow-md ring-2 ring-primary-500/20'
                        : isComplete
                        ? 'border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/20 opacity-70 hover:opacity-100'
                        : 'border-slate-200 dark:border-slate-800 hover:border-primary-400 bg-slate-50/40 dark:bg-slate-800/30'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isLab
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                        }`}
                      >
                        {offering.course_type}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-bold ${
                          isComplete ? 'text-emerald-600' : 'text-slate-500'
                        }`}
                      >
                        {scheduledCount} / {maxMeetings} Scheduled
                      </span>
                    </div>

                    <h3 className="font-bold font-mono text-slate-900 dark:text-white">
                      {offering.course_code}
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 truncate">{offering.course_name}</p>

                    <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px]">
                      <span className="text-slate-500 truncate max-w-[140px]">
                        {asgn ? asgn.professor_name : <span className="text-rose-500">No Professor</span>}
                      </span>
                      <span className="text-slate-400 font-mono">
                        {isLab ? '3-hr continuous' : '1-hr session'}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right 3 Cols: Interactive Weekly Timetable Grid */}
        <div className="xl:col-span-3 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                {activeCohort ? `${activeCohort.branch_code} Sem ${activeCohort.semester_no} Sec ${activeCohort.section_code}` : 'Timetable Grid'}
              </h2>
              <p className="text-xs text-slate-500">
                Weekly master schedule — 8 daily slots (08:30–18:00). Click empty slot to place selected course.
              </p>
            </div>

            {/* Validation Hover Indicator */}
            {hoveredSlot && activeOffering && (
              <div className="flex items-center gap-2 text-xs">
                {isValidating ? (
                  <span className="text-slate-400 flex items-center gap-1">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Validating...
                  </span>
                ) : slotValidation?.allowed ? (
                  <span className="px-2.5 py-1 rounded-full font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Allowed Slot
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Clashes Detected
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Timetable Table Grid */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-slate-200 dark:border-slate-800 text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 font-bold">
                  <th className="p-3 border border-slate-200 dark:border-slate-800 w-28 text-left">Time Slot</th>
                  {WEEKDAYS.map((day) => (
                    <th key={day.id} className="p-3 border border-slate-200 dark:border-slate-800 text-center font-bold">
                      {day.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {SLOTS.map((slot) => {
                  const isLunchBreakSlot = slot.no === 4;
                  return (
                    <React.Fragment key={slot.no}>
                      <tr>
                        {/* Time Column */}
                        <td className="p-2.5 border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 text-slate-500 font-mono text-[11px]">
                          <div className="font-bold text-slate-800 dark:text-slate-200">Slot {slot.no}</div>
                          <div className="text-[10px] text-slate-400">{slot.time}</div>
                        </td>

                        {/* 5 Day Cells for this slot */}
                        {WEEKDAYS.map((day) => {
                          const meeting = meetingsBySlot.get(`${day.id}-${slot.no}`);
                          const isHovered = hoveredSlot?.weekday === day.id && hoveredSlot?.slot_no === slot.no;

                          // Dynamic cell coloring based on hover validation state
                          let cellBg = 'bg-white dark:bg-slate-900';
                          if (isHovered && activeOffering) {
                            if (slotValidation?.allowed) {
                              cellBg = 'bg-emerald-50 dark:bg-emerald-950/40 ring-2 ring-emerald-500 inset-0';
                            } else {
                              cellBg = 'bg-rose-50 dark:bg-rose-950/40 ring-2 ring-rose-500 inset-0';
                            }
                          }

                          return (
                            <td
                              key={day.id}
                              onMouseEnter={() => validateSlotHover(day.id, slot.no)}
                              onMouseLeave={() => setHoveredSlot(null)}
                              onClick={() => handleSlotClick(day.id, slot.no)}
                              className={`p-2 border border-slate-200 dark:border-slate-800 h-20 align-top transition-all cursor-pointer relative ${cellBg}`}
                            >
                              {meeting ? (
                                <div
                                  className={`p-2 rounded-lg border text-[11px] shadow-sm space-y-1 h-full flex flex-col justify-between ${
                                    meeting.course_type === 'LAB'
                                      ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800/60 text-purple-950 dark:text-purple-200'
                                      : 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800/60 text-blue-950 dark:text-blue-200'
                                  }`}
                                >
                                  <div>
                                    <div className="flex items-center justify-between font-bold">
                                      <span className="font-mono">{meeting.course_code}</span>
                                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-white/60 dark:bg-black/30 font-semibold">
                                        R: {meeting.room_no}
                                      </span>
                                    </div>
                                    <p className="truncate font-medium">{meeting.course_name}</p>
                                  </div>

                                  <div className="flex items-center justify-between text-[10px] opacity-80 pt-1 border-t border-black/5 dark:border-white/5">
                                    <span className="truncate">{meeting.professor_name}</span>
                                    {meeting.group_codes && meeting.group_codes.length > 0 && (
                                      <span className="font-mono font-bold">
                                        [{meeting.group_codes.join(', ')}]
                                      </span>
                                    )}
                                  </div>
                                </div>
                              ) : isHovered && activeOffering ? (
                                <div className="text-[11px] text-center pt-2">
                                  {slotValidation?.allowed ? (
                                    <span className="text-emerald-700 dark:text-emerald-300 font-bold">
                                      + Click to Place
                                    </span>
                                  ) : (
                                    <span className="text-rose-600 dark:text-rose-400 font-bold block truncate">
                                      {slotValidation?.conflicts[0]?.type || 'Clash'}
                                    </span>
                                  )}
                                </div>
                              ) : null}
                            </td>
                          );
                        })}
                      </tr>

                      {/* Visual Lunch Break Row (§6 of Architecture Spec) */}
                      {isLunchBreakSlot && (
                        <tr className="bg-amber-50/70 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-center text-[11px] font-semibold">
                          <td className="p-2 border border-slate-200 dark:border-slate-800 flex items-center justify-center gap-1 font-mono">
                            <Coffee className="w-3.5 h-3.5" /> 12:30–14:00
                          </td>
                          <td colSpan={5} className="p-2 border border-slate-200 dark:border-slate-800">
                            ☕ Mandatory University Lunch Break — No lectures or laboratory sessions permitted
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Meeting Detail Modal */}
      {isDetailModalOpen && selectedMeeting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Scheduled Lecture Details</span>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  {selectedMeeting.course_code} — {selectedMeeting.course_name}
                </h2>
              </div>
              <button onClick={() => setIsDetailModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Faculty Professor</span>
                <span className="font-bold">{selectedMeeting.professor_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Day & Time</span>
                <span className="font-bold">
                  {selectedMeeting.weekday_display} (Slots {selectedMeeting.start_slot} to {selectedMeeting.end_slot})
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Duration</span>
                <span className="font-bold">{selectedMeeting.duration_slots} Hour(s)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Current Room</span>
                <span className="font-bold font-mono">
                  Room {selectedMeeting.room_no} ({selectedMeeting.building_code})
                </span>
              </div>
              {selectedMeeting.group_codes && selectedMeeting.group_codes.length > 0 && (
                <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Target Student Group</span>
                  <span className="font-bold font-mono text-primary-600">
                    {selectedMeeting.group_codes.join(', ')}
                  </span>
                </div>
              )}
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={() => {
                  if (confirm(`Remove scheduled meeting for ${selectedMeeting.course_code}?`)) {
                    deleteMeetingMutation.mutate(selectedMeeting.id);
                  }
                }}
                className="px-3 py-1.5 rounded-lg text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 font-semibold flex items-center gap-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Meeting</span>
              </button>

              <button
                onClick={() => setIsDetailModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Version Modal */}
      {isCreateVersionOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Create Schedule Version</h2>
              <button onClick={() => setIsCreateVersionOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Version Title</label>
                <input
                  type="text"
                  placeholder="e.g. Draft 2 - Optimized Labs"
                  value={newVersionName}
                  onChange={(e) => setNewVersionName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button onClick={() => setIsCreateVersionOpen(false)} className="px-3 py-1.5 rounded-lg text-slate-600">
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (!activeTerm) return;
                    createVersionMutation.mutate({
                      term: activeTerm.id,
                      name: newVersionName,
                      status: 'DRAFT',
                    });
                  }}
                  className="px-4 py-1.5 rounded-lg bg-primary-600 text-white font-semibold"
                >
                  Create Draft
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Phase 5 Modals */}
      <AutoGenerateModal
        isOpen={isAutoGenerateModalOpen}
        onClose={() => setIsAutoGenerateModalOpen(false)}
        branches={branches}
        onStartGeneration={handleStartGeneration}
      />

      <GenerationProgressModal
        isOpen={isProgressModalOpen}
        taskId={activeTaskId}
        onComplete={handleGenerationComplete}
        onCancel={() => {
          setIsProgressModalOpen(false);
          setActiveTaskId(null);
        }}
      />

      <ProposalPreviewModal
        isOpen={isPreviewModalOpen}
        proposal={selectedProposal}
        onClose={() => setIsPreviewModalOpen(false)}
        onCommit={handleCommitProposal}
        onDiscard={handleDiscardProposal}
        isCommitting={isCommittingProposal}
        isDiscarding={isDiscardingProposal}
      />
    </div>
  );
};
