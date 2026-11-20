import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  Calendar,
  Clock,
  Plus,
  Trash2,
  X,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  CalendarCog,
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
  Building2,
  GraduationCap,
  Layers,
  BookOpen,
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
  Department,
  AcademicTerm,
  Room,
  AutoScheduleProposal,
} from '../types';
import { pickCurrentTerm } from '../utils/terms';

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
  // Mandatory lunch break between 4 and 5 (12:30 - 14:00)
  { no: 5, time: '14:00 - 15:00', session: 'AFTERNOON' },
  { no: 6, time: '15:00 - 16:00', session: 'AFTERNOON' },
  { no: 7, time: '16:00 - 17:00', session: 'AFTERNOON' },
  { no: 8, time: '17:00 - 18:00', session: 'AFTERNOON' },
];

export const TimetablePlannerPage: React.FC = () => {
  const queryClient = useQueryClient();

  // 1. Cascading Academic Hierarchy Selection States
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | undefined>();
  const [selectedBranchId, setSelectedBranchId] = useState<number | undefined>();
  const [selectedSemester, setSelectedSemester] = useState<number | undefined>();
  const [selectedCohortId, setSelectedCohortId] = useState<number | undefined>();
  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();
  const [termCycle, setTermCycle] = useState<'ODD' | 'EVEN'>('ODD');
  const [selectedVersionId, setSelectedVersionId] = useState<number | undefined>();
  const [selectedRoomId, setSelectedRoomId] = useState<number | undefined>();

  // 2. Dragging / Active placement state
  const [activeOffering, setActiveOffering] = useState<CourseOffering | null>(null);
  const [activeAssignment, setActiveAssignment] = useState<TeachingAssignment | null>(null);

  // 3. Hover / slot validation state
  const [hoveredSlot, setHoveredSlot] = useState<{ weekday: number; slot_no: number } | null>(null);
  const [slotValidation, setSlotValidation] = useState<ValidationResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // 4. Modal / Detail state
  const [selectedMeeting, setSelectedMeeting] = useState<ScheduledMeeting | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Auto-dismiss conflict message after 7 seconds without layout shifting
  useEffect(() => {
    if (!errorMessage) return;
    const timer = setTimeout(() => {
      setErrorMessage(null);
    }, 7000);
    return () => clearTimeout(timer);
  }, [errorMessage]);

  // 5. Phase 5 Auto-Scheduler State
  const [isAutoGenerateModalOpen, setIsAutoGenerateModalOpen] = useState(false);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<AutoScheduleProposal | null>(null);
  const [isCommittingProposal, setIsCommittingProposal] = useState(false);
  const [isDiscardingProposal, setIsDiscardingProposal] = useState(false);

  // -------------------------------------------------------------
  // Data Queries
  // -------------------------------------------------------------

  // Departments Query
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: () => academicsService.getDepartments(),
  });

  const activeDepartment =
    departments.find((d) => d.id === selectedDepartmentId) || departments[0];

  // Branches Query
  const { data: branches = [] } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  // Filter branches by active department
  const departmentBranches = useMemo(() => {
    if (!activeDepartment) return branches;
    const filtered = branches.filter((b) => b.department === activeDepartment.id);
    return filtered.length > 0 ? filtered : branches;
  }, [branches, activeDepartment]);

  const activeBranch =
    departmentBranches.find((b) => b.id === selectedBranchId) || departmentBranches[0] || branches[0];

  // Academic Terms Query
  const { data: terms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const activeTerm = terms.find((t) => t.id === selectedTermId) || pickCurrentTerm(terms);

  // Sync termCycle with activeTerm.term_type when activeTerm loads or changes
  useEffect(() => {
    if (activeTerm?.term_type === 'ODD' || activeTerm?.term_type === 'EVEN') {
      setTermCycle(activeTerm.term_type);
    }
  }, [activeTerm?.term_type, activeTerm?.id]);

  // Handler to switch cycle and automatically select matching term if available
  const handleCycleChange = (cycle: 'ODD' | 'EVEN') => {
    setTermCycle(cycle);
    const matchingTerm = terms.find((t) => t.term_type === cycle);
    if (matchingTerm && matchingTerm.id !== selectedTermId) {
      setSelectedTermId(matchingTerm.id);
      setSelectedVersionId(undefined);
      setSelectedCohortId(undefined);
    }
  };

  // Semesters for activeBranch filtered strictly by Odd / Even semester cycle
  const maxSemesters = activeBranch?.max_semesters || 8;
  const allSemesterNumbers = useMemo(() => {
    return Array.from({ length: maxSemesters }, (_, i) => i + 1);
  }, [maxSemesters]);

  const semesterOptions = useMemo(() => {
    if (termCycle === 'ODD') {
      return allSemesterNumbers.filter((sem) => sem % 2 === 1);
    }
    if (termCycle === 'EVEN') {
      return allSemesterNumbers.filter((sem) => sem % 2 === 0);
    }
    return allSemesterNumbers;
  }, [allSemesterNumbers, termCycle]);

  // Default active semester based on branch and filtered semesterOptions
  const activeSemester =
    selectedSemester !== undefined && semesterOptions.includes(selectedSemester)
      ? selectedSemester
      : semesterOptions[0] || (termCycle === 'EVEN' ? 2 : 1);

  // Auto-switch selectedSemester if current semester does not belong to the active cycle
  useEffect(() => {
    if (semesterOptions.length > 0) {
      if (selectedSemester === undefined || !semesterOptions.includes(selectedSemester)) {
        setSelectedSemester(semesterOptions[0]);
        setSelectedCohortId(undefined);
      }
    }
  }, [semesterOptions, selectedSemester]);

  // Schedule Versions Query (Internal - resolved automatically behind the scenes)
  const { data: versions = [], refetch: refetchVersions, isLoading: isVersionsLoading } = useQuery({
    queryKey: ['timetable-versions', activeTerm?.id],
    queryFn: () => timetableService.getVersions(activeTerm?.id),
    enabled: !!activeTerm,
  });

  const activeVersion = versions.find((v) => v.id === selectedVersionId) || versions[0];
  const [isAutoCreatingVersion, setIsAutoCreatingVersion] = useState(false);

  // Automatically ensure a default schedule exists for active term so user doesn't need to manage versions
  useEffect(() => {
    if (activeTerm?.id && !isVersionsLoading && versions.length === 0 && !isAutoCreatingVersion) {
      setIsAutoCreatingVersion(true);
      timetableService.createVersion({
        term: activeTerm.id as any,
        name: `Schedule - ${activeTerm.name}`,
        status: 'DRAFT',
      }).then((newVer) => {
        refetchVersions();
        setSelectedVersionId(newVer.id);
      }).catch((err) => {
        console.error('Failed to auto-create schedule for term:', err);
      }).finally(() => {
        setIsAutoCreatingVersion(false);
      });
    }
  }, [activeTerm?.id, versions.length, isVersionsLoading, isAutoCreatingVersion, refetchVersions]);

  // Cohorts Query for this term
  const { data: allCohorts = [], refetch: refetchCohorts, isSuccess: cohortsLoaded } = useQuery({
    queryKey: ['cohorts', activeTerm?.id],
    queryFn: () => academicsService.getCohorts({ term: activeTerm?.id }),
    enabled: !!activeTerm,
  });

  // Filter matching cohorts for current activeBranch & activeSemester
  const matchingCohorts = useMemo(() => {
    return allCohorts.filter((c) => {
      const matchBranch = activeBranch ? c.branch === activeBranch.id : true;
      const matchSem = activeSemester !== undefined ? c.semester_no === activeSemester : true;
      return matchBranch && matchSem;
    });
  }, [allCohorts, activeBranch, activeSemester]);

  // Active cohort MUST strictly belong to the matching cohorts for activeBranch & activeSemester
  const activeCohort =
    matchingCohorts.find((c) => c.id === selectedCohortId) ||
    matchingCohorts[0] ||
    null;

  // Auto-create cohort Section A if it doesn't exist yet for selected course/branch and semester in this term
  const [isAutoCreatingCohort, setIsAutoCreatingCohort] = useState(false);
  useEffect(() => {
    if (
      activeBranch?.id &&
      activeTerm?.id &&
      activeSemester !== undefined &&
      cohortsLoaded &&
      matchingCohorts.length === 0 &&
      !isAutoCreatingCohort
    ) {
      setIsAutoCreatingCohort(true);
      academicsService
        .createCohort({
          branch: activeBranch.id,
          term: activeTerm.id,
          semester_no: activeSemester,
          section_code: 'A',
          student_count: 60,
        })
        .then((newCohort) => {
          refetchCohorts();
          setSelectedCohortId(newCohort.id);
        })
        .catch((err) => {
          console.warn('Could not auto-create batch for branch and semester:', err);
        })
        .finally(() => {
          setIsAutoCreatingCohort(false);
        });
    }
  }, [
    activeBranch?.id,
    activeTerm?.id,
    activeSemester,
    matchingCohorts.length,
    cohortsLoaded,
    isAutoCreatingCohort,
    refetchCohorts,
  ]);

  // Rooms Query
  const { data: rooms = [] } = useQuery({
    queryKey: ['rooms'],
    queryFn: () => facilitiesService.getRooms(),
  });

  // Filter rooms based on active offering course type:
  // - If LAB class: only show laboratory rooms (COMPUTER_LAB, ELECTRONICS_LAB, CHEMISTRY_LAB)
  // - If THEORY class (or SEMINAR/PROJECT): only show lecture rooms (CLASSROOM, SEMINAR_HALL)
  // - If no subject is active: show all rooms
  const filteredRooms = useMemo(() => {
    if (!activeOffering) return rooms;

    const isLab = activeOffering.course_type === 'LAB';
    if (isLab) {
      const labRooms = rooms.filter(
        (r) =>
          r.room_type === 'COMPUTER_LAB' ||
          r.room_type === 'ELECTRONICS_LAB' ||
          r.room_type === 'CHEMISTRY_LAB' ||
          (r.room_type && r.room_type.includes('LAB'))
      );
      return labRooms.length > 0 ? labRooms : rooms;
    } else {
      const theoryRooms = rooms.filter(
        (r) =>
          r.room_type === 'CLASSROOM' ||
          r.room_type === 'SEMINAR_HALL' ||
          !(r.room_type && r.room_type.includes('LAB'))
      );
      return theoryRooms.length > 0 ? theoryRooms : rooms;
    }
  }, [rooms, activeOffering]);

  // Ensure selected room is valid and belongs to filteredRooms
  useEffect(() => {
    if (filteredRooms.length === 0) return;
    const isCurrentRoomInFiltered = filteredRooms.some((r) => r.id === selectedRoomId);
    if (!isCurrentRoomInFiltered) {
      setSelectedRoomId(filteredRooms[0].id);
    }
  }, [filteredRooms, selectedRoomId]);

  const activeRoom = filteredRooms.find((r) => r.id === selectedRoomId) || filteredRooms[0] || rooms[0];

  // Timetable Grid Query
  const { data: gridData, refetch: refetchGrid } = useQuery({
    queryKey: ['timetable-grid', activeVersion?.id, activeCohort?.id],
    placeholderData: keepPreviousData,
    queryFn: () =>
      activeVersion
        ? timetableService.getGrid(activeVersion.id, { cohort_id: activeCohort?.id })
        : Promise.resolve({
            schedule_version_id: 0,
            revision: 1,
            status: 'DRAFT' as const,
            meetings: [],
            total_count: 0,
          }),
    enabled: !!activeVersion,
  });

  // Course Offerings Query for cohort
  const { data: offerings = [], isSuccess: offeringsLoaded, isPlaceholderData: offeringsArePrevious } = useQuery({
    queryKey: ['course-offerings', activeCohort?.id],
    placeholderData: keepPreviousData,
    queryFn: () => academicsService.getCourseOfferings({ cohort: activeCohort?.id }),
    enabled: !!activeCohort,
  });

  // Filter offerings to ONLY subjects strictly belonging to the active course/branch and activeSemester
  const semesterOfferings = useMemo(() => {
    if (!activeCohort) return [];
    return offerings.filter((offering) => {
      if (offering.cohort !== activeCohort.id) return false;
      if (offering.semester_no !== undefined) {
        return offering.semester_no === activeSemester;
      }
      return true;
    });
  }, [offerings, activeCohort, activeSemester]);

  // Reset active placement selection if activeSemester or branch changes
  useEffect(() => {
    setActiveOffering(null);
    setActiveAssignment(null);
  }, [activeSemester, activeBranch?.id]);

  // Teaching Assignments Query for cohort
  const { data: assignments = [] } = useQuery({
    queryKey: ['teaching-assignments', activeCohort?.id],
    placeholderData: keepPreviousData,
    queryFn: () => academicsService.getTeachingAssignments({ cohort: activeCohort?.id }),
    enabled: !!activeCohort,
  });

  // Schedule Quality Score Query
  const { data: qualityScoreData, refetch: refetchScore } = useQuery({
    queryKey: ['timetable-score', activeVersion?.id],
    placeholderData: keepPreviousData,
    queryFn: () => (activeVersion ? schedulerService.getTimetableScore(activeVersion.id) : null),
    enabled: !!activeVersion,
  });

  // -------------------------------------------------------------
  // Mutations & Collision Handlers
  // -------------------------------------------------------------

  const extractConflictMessage = (err: any): string => {
    const data = err.response?.data;
    if (!data) return err.message || 'Conflict detected! Unable to place meeting.';
    if (typeof data === 'string') return data;
    if (typeof data.detail === 'string') return data.detail;
    if (typeof data.detail?.detail === 'string') return data.detail.detail;

    const conflicts = data.conflicts || data.detail?.conflicts;
    if (Array.isArray(conflicts) && conflicts.length > 0) {
      return conflicts.map((c: any) => c.message || c.type).join(' | ');
    }

    return 'Collision or constraint conflict detected.';
  };

  const populateCurriculumMutation = useMutation({
    mutationFn: (cohortId: number) => academicsService.populateFromCurriculum(cohortId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-offerings', activeCohort?.id] });
      setSuccessToast('Populated course offerings from curriculum successfully!');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(extractConflictMessage(err));
    },
  });

  // Auto-populate offerings from curriculum & semester courses when cohort has no offerings yet
  const autoPopulatedCohortRef = React.useRef<Set<number>>(new Set());
  useEffect(() => {
    if (activeCohort?.id && offeringsLoaded && !offeringsArePrevious && offerings.length === 0 && !autoPopulatedCohortRef.current.has(activeCohort.id)) {
      autoPopulatedCohortRef.current.add(activeCohort.id);
      academicsService.populateFromCurriculum(activeCohort.id).then(() => {
        queryClient.invalidateQueries({ queryKey: ['course-offerings', activeCohort.id] });
      }).catch((err) => {
        console.warn('Auto-populate from curriculum skipped:', err);
      });
    }
  }, [activeCohort?.id, offeringsLoaded, offeringsArePrevious, offerings.length, queryClient]);

  const createCohortMutation = useMutation({
    mutationFn: (data: Partial<Cohort>) => academicsService.createCohort(data),
    onSuccess: (newCohort) => {
      refetchCohorts();
      setSelectedCohortId(newCohort.id);
      setSuccessToast(`Created Batch ${newCohort.section_code} successfully!`);
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(extractConflictMessage(err));
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
      setErrorMessage(null);
      setSuccessToast('Meeting placed and reservations locked successfully!');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      const msg = extractConflictMessage(err);
      setErrorMessage(msg);
    },
  });

  const deleteMeetingMutation = useMutation({
    mutationFn: (id: number) => timetableService.deleteMeeting(id),
    onSuccess: () => {
      refetchGrid();
      setIsDetailModalOpen(false);
      setSelectedMeeting(null);
      setErrorMessage(null);
      setSuccessToast('Meeting removed and reservations released.');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(extractConflictMessage(err));
    },
  });

  const { user } = useAuth();
  const isSuperAdmin = user?.is_superuser || user?.roles?.includes('SUPER_ADMIN');
  const isLocked =
    activeVersion?.status === 'PUBLISHED' ||
    (activeVersion?.status === 'UNDER_REVIEW' && !isSuperAdmin);

  // WebSocket Live Updates
  const { isConnected } = useTimetableSocket(activeVersion?.id, {
    onEvent: (event) => {
      if (event.type === 'schedule.published') {
        setSuccessToast(`Schedule has been officially PUBLISHED!`);
        setTimeout(() => setSuccessToast(null), 5000);
      }
    },
  });

  const submitReviewMutation = useMutation({
    mutationFn: (id: number) => timetableService.submitReview(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast('Schedule submitted for administrative review!');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(extractConflictMessage(err));
    },
  });

  const sendBackMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      timetableService.sendBackToDraft(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast('Schedule returned to draft status.');
      setTimeout(() => setSuccessToast(null), 3000);
    },
    onError: (err: any) => {
      setErrorMessage(extractConflictMessage(err));
    },
  });

  const publishMutation = useMutation({
    mutationFn: (id: number) => timetableService.publishSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
      setSuccessToast('Timetable officially PUBLISHED! Clashes resolved.');
      setTimeout(() => setSuccessToast(null), 4000);
    },
    onError: (err: any) => {
      setErrorMessage(extractConflictMessage(err));
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
      setErrorMessage(extractConflictMessage(err));
    }
  };

  const handleGenerationComplete = async (proposalId: number) => {
    if (!activeVersion) return;
    try {
      const prop = await schedulerService.getProposal(activeVersion.id, proposalId);
      setIsProgressModalOpen(false);
      setSelectedProposal(prop);
      setIsPreviewModalOpen(true);
    } catch (err: any) {
      setErrorMessage(extractConflictMessage(err));
    }
  };

  const handleCommitProposal = async () => {
    if (!selectedProposal || !activeVersion) return;
    setIsCommittingProposal(true);
    try {
      await schedulerService.commitProposal(activeVersion.id, selectedProposal.id);
      setIsPreviewModalOpen(false);
      setSelectedProposal(null);
      refetchGrid();
      refetchScore();
      setSuccessToast('AI Schedule successfully committed to timetable!');
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      setErrorMessage(extractConflictMessage(err));
    } finally {
      setIsCommittingProposal(false);
    }
  };

  const handleDiscardProposal = async () => {
    if (!selectedProposal || !activeVersion) return;
    setIsDiscardingProposal(true);
    try {
      await schedulerService.discardProposal(activeVersion.id, selectedProposal.id);
      setIsPreviewModalOpen(false);
      setSelectedProposal(null);
      setSuccessToast('Generated proposal discarded.');
      setTimeout(() => setSuccessToast(null), 3000);
    } catch (err: any) {
      setErrorMessage(extractConflictMessage(err));
    } finally {
      setIsDiscardingProposal(false);
    }
  };

  // -------------------------------------------------------------
  // Grid Meetings Lookup & Calculations
  // -------------------------------------------------------------

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

  // Debounced slot hover validation with stale response cancellation
  const hoverTimeoutRef = React.useRef<any>(null);
  const currentValidationKeyRef = React.useRef<string>('');

  const validateSlotHover = (weekday: number, slot_no: number) => {
    if (!activeAssignment || !activeVersion || !selectedRoomId) return;

    setHoveredSlot({ weekday, slot_no });

    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    const slotKey = `${weekday}-${slot_no}-${activeAssignment.id}-${selectedRoomId}`;
    currentValidationKeyRef.current = slotKey;

    hoverTimeoutRef.current = setTimeout(async () => {
      const isLab = activeOffering?.course_type === 'LAB';
      const duration = isLab ? 3 : 1;

      try {
        setIsValidating(true);
        const result = await timetableService.validatePlacement({
          schedule_version_id: activeVersion.id,
          teaching_assignment_id: activeAssignment.id,
          weekday,
          start_slot: slot_no,
          duration_slots: duration,
          room_id: selectedRoomId,
        });

        // Only commit result if user is still hovering this exact slot
        if (currentValidationKeyRef.current === slotKey) {
          setSlotValidation(result);
        }
      } catch {
        if (currentValidationKeyRef.current === slotKey) {
          setSlotValidation({
            allowed: false,
            conflicts: [{ type: 'API_ERROR', message: 'Validation request failed' }],
          });
        }
      } finally {
        if (currentValidationKeyRef.current === slotKey) {
          setIsValidating(false);
        }
      }
    }, 100);
  };

  const handleSlotMouseLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    currentValidationKeyRef.current = '';
    setHoveredSlot(null);
    setSlotValidation(null);
    setIsValidating(false);
  };

  const handleSlotClick = (weekday: number, slot_no: number) => {
    // 1. If an existing meeting is already in that cell, open details
    const existing = meetingsBySlot.get(`${weekday}-${slot_no}`);
    if (existing) {
      setSelectedMeeting(existing);
      setIsDetailModalOpen(true);
      return;
    }

    if (isLocked) {
      setErrorMessage(
        `Schedule is currently ${activeVersion?.status}. Modifications are locked.`
      );
      return;
    }

    // 2. Validate prerequisites before placement
    if (!activeOffering) {
      setErrorMessage('Please select a course/subject from the left panel first.');
      return;
    }

    if (!activeAssignment) {
      setErrorMessage(
        `No professor assigned to ${activeOffering.course_code}. Please assign a teacher in Teaching Assignments first.`
      );
      return;
    }

    if (!selectedRoomId) {
      setErrorMessage('Please select a target room number from the room list.');
      return;
    }

    if (!activeVersion) {
      setErrorMessage('Initializing timetable schedule. Please try again in a moment.');
      return;
    }

    // 3. Place meeting (error will be cleared on success or updated on conflict)
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
  };

  const selectOfferingForPlacement = (offering: CourseOffering) => {
    const asgn = assignments.find((a) => a.course_offering === offering.id);
    if (!asgn) {
      setErrorMessage(
        `No professor assigned to ${offering.course_code} (${offering.course_name}) yet! Please assign a faculty member first.`
      );
      return;
    }

    setActiveOffering(offering);
    setActiveAssignment(asgn);
    setErrorMessage(null);

    // Automatically switch to a compatible room for this offering type
    const isLab = offering.course_type === 'LAB';
    const compatible = rooms.filter((r) =>
      isLab
        ? r.room_type === 'COMPUTER_LAB' || r.room_type === 'ELECTRONICS_LAB' || r.room_type === 'CHEMISTRY_LAB' || (r.room_type && r.room_type.includes('LAB'))
        : r.room_type === 'CLASSROOM' || r.room_type === 'SEMINAR_HALL' || !(r.room_type && r.room_type.includes('LAB'))
    );
    const currentRoom = rooms.find((r) => r.id === selectedRoomId);
    if (!currentRoom || !compatible.some((r) => r.id === currentRoom.id)) {
      if (compatible.length > 0) {
        setSelectedRoomId(compatible[0].id);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Floating Notifications Overlay (Fixed to top-right to prevent grid layout shifting & flickering) */}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none">
        {successToast && (
          <div className="pointer-events-auto flex items-center gap-2 px-4 py-3 rounded-md bg-emerald-600 text-white text-xs font-semibold border border-emerald-500 transition-colors duration-200">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{successToast}</span>
          </div>
        )}

        {errorMessage && (
          <div className="pointer-events-auto bg-rose-50 dark:bg-rose-950/95 border-2 border-rose-500/80 dark:border-rose-600 rounded-lg p-4 transition-colors duration-200">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-md bg-rose-100 dark:bg-rose-900/60 text-rose-600 dark:text-rose-300 flex-shrink-0 mt-0.5">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div className="text-xs">
                  <h4 className="font-semibold text-rose-900 dark:text-rose-100 text-sm">
                    Placement Conflict
                  </h4>
                  <p className="mt-1 text-rose-800 dark:text-rose-200 font-medium leading-relaxed">
                    {errorMessage}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setErrorMessage(null)}
                className="text-rose-400 hover:text-rose-700 dark:hover:text-rose-200 p-1.5 rounded-lg hover:bg-rose-100 dark:hover:bg-rose-900/40 transition-colors"
                title="Dismiss"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Top Header & Overview */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 mb-2">
            <CalendarCog className="w-3.5 h-3.5 text-amber-500" />
            <span>University Timetable Planner with Collision Prevention</span>
          </div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
            Timetable Planner
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Select Department, Course, Semester, and Room to place subjects on the master weekly grid with hard teacher & room clash protection.
          </p>
        </div>

        {/* Action Controls & Live Sync */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Quality Score Badge */}
          {qualityScoreData && (
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800 "
              title="Schedule Quality Score"
            >
              <Award className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Score: {qualityScoreData.overall_score.toFixed(1)}/100</span>
            </div>
          )}

          {/* WebSocket Status Indicator */}
          {isConnected ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Live Sync</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
              <span className="w-2 h-2 rounded-full bg-slate-400"></span>
              <span>Connecting...</span>
            </div>
          )}

          {/* Phase 5 Auto-Generate Button */}
          {isAuthorizedToAutoSchedule && activeVersion?.status === 'DRAFT' && (
            <button
              onClick={() => setIsAutoGenerateModalOpen(true)}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white transition-colors flex items-center gap-1.5"
              title="Smart automatic timetable generator with Google OR-Tools"
            >
              <CalendarCog className="w-4 h-4 text-amber-300" />
              <span>Auto-Generate</span>
            </button>
          )}

          {/* Workflow Action Buttons */}
          {activeVersion?.status === 'DRAFT' && (
            <button
              onClick={() => {
                if (
                  confirm(
                    `Submit schedule for Administrative Review?`
                  )
                ) {
                  submitReviewMutation.mutate(activeVersion.id);
                }
              }}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-700 text-white transition-colors flex items-center gap-1.5"
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
                  if (confirm(`Run clash verification and PUBLISH schedule?`)) {
                    publishMutation.mutate(activeVersion.id);
                  }
                }}
                className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors flex items-center gap-1.5"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Approve & Publish</span>
              </button>
            </>
          )}

          {activeVersion?.status === 'PUBLISHED' && (
            <span className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>PUBLISHED (Locked)</span>
            </span>
          )}
        </div>
      </div>

      {/* Lock Notice Banner */}
      {isLocked && (
        <div className="p-3.5 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs font-semibold text-amber-800 dark:text-amber-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            {activeVersion?.status === 'PUBLISHED'
              ? 'This timetable is officially PUBLISHED. Changes are locked.'
              : 'This timetable is currently UNDER_REVIEW by administration. Coordinators cannot edit meetings during review.'}
          </span>
        </div>
      )}

      {/* ============================================================== */}
      {/* Top Academic Selection Pipeline (Department -> Course -> Semester -> Room) */}
      {/* ============================================================== */}
      <div className="p-5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 text-xs font-semibold">
              1
            </span>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200">
              University Academic Pathway & Target Room
            </span>
          </div>
          <span className="text-[11px] text-slate-400">
            Hierarchical Academic Selection Workflow
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* 1. Department */}
          <div>
            <label className="flex items-center gap-1.5 h-5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              <Building2 className="w-3.5 h-3.5 text-primary-600" />
              <span>Department</span>
            </label>
            <select
              value={activeDepartment?.id || ''}
              onChange={(e) => {
                const newDeptId = Number(e.target.value);
                setSelectedDepartmentId(newDeptId);
                const deptBranches = branches.filter((b) => b.department === newDeptId);
                if (deptBranches.length > 0) {
                  setSelectedBranchId(deptBranches[0].id);
                }
                setSelectedCohortId(undefined);
              }}
              className="w-full px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none"
            >
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          {/* 2. Course / Degree / Branch */}
          <div>
            <label className="flex items-center gap-1.5 h-5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              <GraduationCap className="w-3.5 h-3.5 text-indigo-600" />
              <span>Course / Degree</span>
            </label>
            <select
              value={activeBranch?.id || ''}
              onChange={(e) => {
                const newBranchId = Number(e.target.value);
                setSelectedBranchId(newBranchId);
                setSelectedCohortId(undefined);
              }}
              disabled={departmentBranches.length === 0}
              className="w-full px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none disabled:opacity-50"
            >
              {departmentBranches.length === 0 ? (
                <option value="">No courses in this department</option>
              ) : (
                departmentBranches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.code}) — {b.degree_name}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* 3. Semester */}
          <div>
            <div className="flex items-center justify-between h-5 mb-1.5">
              <label className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                <Layers className="w-3.5 h-3.5 text-amber-600" />
                <span>Semester</span>
              </label>
              {/* Odd / Even semester cycle selection */}
              <div className="inline-flex h-5 items-center rounded-md p-px bg-slate-100 dark:bg-slate-800 text-[10px] leading-none font-semibold border border-slate-200 dark:border-slate-700">
                <button
                  type="button"
                  onClick={() => handleCycleChange('ODD')}
                  className={`px-2 py-[3px] rounded transition-colors ${
                    termCycle === 'ODD'
                      ? 'bg-amber-500 text-white '
                      : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                  }`}
                  title="Show Odd Semesters (1, 3, 5, 7...)"
                >
                  Odd
                </button>
                <button
                  type="button"
                  onClick={() => handleCycleChange('EVEN')}
                  className={`px-2 py-[3px] rounded transition-colors ${
                    termCycle === 'EVEN'
                      ? 'bg-amber-500 text-white '
                      : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                  }`}
                  title="Show Even Semesters (2, 4, 6, 8...)"
                >
                  Even
                </button>
              </div>
            </div>
            <select
              value={activeSemester}
              onChange={(e) => {
                setSelectedSemester(Number(e.target.value));
                setSelectedCohortId(undefined);
              }}
              className="w-full px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none"
            >
              {semesterOptions.map((sem) => (
                <option key={sem} value={sem}>
                  Semester {sem} ({sem % 2 === 1 ? 'Odd' : 'Even'})
                </option>
              ))}
            </select>
          </div>

          {/* 4. Target Room Selector */}
          <div>
            <label className="flex items-center justify-between h-5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              <span className="flex items-center gap-1.5">
                <DoorOpen className="w-3.5 h-3.5 text-purple-600" />
                <span>Target Room</span>
                {activeOffering && (
                  <span
                    className={`text-[10px] leading-none px-2 py-1 rounded font-semibold uppercase tracking-wider ${
                      activeOffering.course_type === 'LAB'
                        ? 'bg-purple-100 dark:bg-purple-950/80 text-purple-800 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                        : 'bg-blue-100 dark:bg-blue-950/80 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                    }`}
                  >
                    {activeOffering.course_type === 'LAB'? 'Labs Only': 'Classrooms Only'}
                  </span>
                )}
              </span>
              {activeRoom && (
                <span className="text-[10px] font-mono text-purple-600 dark:text-purple-400">
                  Cap: {activeRoom.capacity}
                </span>
              )}
            </label>
            <select
              value={selectedRoomId || ''}
              onChange={(e) => setSelectedRoomId(Number(e.target.value))}
              className="w-full px-3 py-2 text-xs rounded-md border border-purple-200 dark:border-purple-800/80 bg-purple-50/50 dark:bg-purple-950/30 font-semibold focus:ring-1 focus:ring-purple-500 focus:outline-none text-purple-950 dark:text-purple-200"
            >
              {filteredRooms.map((r) => (
                <option key={r.id} value={r.id}>
                  Room {r.room_no} ({r.building_code}) — {r.room_type_display} [Cap: {r.capacity}]
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-400 mt-1 h-4 leading-4 truncate">
              {activeOffering ? (
                <>
                  Showing {filteredRooms.length}{' '}
                  {activeOffering.course_type === 'LAB' ? 'lab' : 'theory'} room(s) for{' '}
                  <strong className="text-slate-600 dark:text-slate-300">
                    {activeOffering.course_code}
                  </strong>
                </>
              ) : (
                <>Showing all {filteredRooms.length} room(s)</>
              )}
            </p>
          </div>
        </div>

        {/* Secondary Bar: Academic Term & Active Selection */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex flex-wrap items-center gap-4">
            {/* Term */}
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-slate-500">Term:</span>
              <select
                value={activeTerm?.id || ''}
                onChange={(e) => {
                  const newTermId = Number(e.target.value);
                  setSelectedTermId(newTermId);
                  setSelectedVersionId(undefined);
                  setSelectedCohortId(undefined);
                  const chosenTerm = terms.find((t) => t.id === newTermId);
                  if (chosenTerm && (chosenTerm.term_type === 'ODD' || chosenTerm.term_type === 'EVEN')) {
                    setTermCycle(chosenTerm.term_type);
                  }
                }}
                className="px-2.5 py-1 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-medium"
              >
                {terms.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.term_type_display || t.term_type})
                  </option>
                ))}
              </select>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                  termCycle === 'ODD'
                    ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                    : 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                }`}
              >
                {termCycle === 'ODD' ? 'Odd Semesters Cycle' : 'Even Semesters Cycle'}
              </span>
            </div>
          </div>

          {/* Active selection summary pill */}
          <div className="text-[11px] text-slate-500 font-medium flex items-center gap-2">
            <span>Viewing:</span>
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 font-mono font-semibold text-slate-800 dark:text-slate-200">
              {activeBranch?.code} • Sem {activeSemester}
            </span>
          </div>
        </div>
      </div>



      {/* ============================================================== */}
      {/* Main Layout: Left Subjects Palette + Right Weekly Timetable Grid */}
      {/* ============================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)] gap-6 items-start">
        {/* Left Column: Subjects for Selected Course & Semester */}
        <div className="min-w-0 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-primary-600" />
                <span className="whitespace-nowrap">Subjects</span>
              </h2>
              <p className="text-[11px] text-slate-500">
                {activeBranch?.code} Sem {activeSemester}
              </p>
            </div>
            <span className="text-xs font-mono font-semibold text-slate-400 whitespace-nowrap">
              {semesterOfferings.length} total
            </span>
          </div>

          {/* Active Placement Indicator Card: always rendered at a fixed height so
              picking a subject never pushes the list (and the clicked card) down. */}
          {activeOffering ? (
            <div className="h-[164px] p-3.5 rounded-md bg-primary-50 dark:bg-primary-950/60 border border-primary-300 dark:border-primary-800 text-xs space-y-1.5 overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-primary-900 dark:text-primary-200 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-600"></span>
                  Placing subject
                </span>
                <button
                  onClick={() => {
                    setActiveOffering(null);
                    setActiveAssignment(null);
                  }}
                  className="text-primary-600 hover:text-primary-800 dark:text-primary-400 font-semibold text-[11px]"
                >
                  Cancel
                </button>
              </div>
              <p className="font-mono font-semibold text-slate-900 dark:text-white truncate">
                {activeOffering.course_code} — {activeOffering.course_name}
              </p>
              <div className="text-[11px] text-slate-600 dark:text-slate-300 flex flex-col gap-0.5 pt-1">
                <span className="truncate">
                  <strong>Faculty:</strong> {activeAssignment?.professor_name || 'Assigned Professor'}
                </span>
                <span className="truncate">
                  <strong>Target Room:</strong> Room {activeRoom?.room_no} ({activeRoom?.room_type_display})
                </span>
                <span className="truncate">
                  <strong>Pattern:</strong>{' '}
                  {activeOffering.course_type === 'LAB'
                    ? '2 × 3h Continuous Lab'
                    : `${activeOffering.course_credit || 3} × 1h Theory`}
                </span>
              </div>
              <p className="text-[10px] text-primary-700 dark:text-primary-300 font-semibold pt-1 truncate">
                Click an empty slot on the timetable to place this class.
              </p>
            </div>
          ) : (
            <div className="h-[164px] p-3.5 rounded-md border border-dashed border-slate-300 dark:border-slate-700 text-xs flex flex-col justify-center gap-1 text-slate-500">
              <span className="font-semibold text-slate-700 dark:text-slate-300">No subject selected</span>
              <span>Pick a subject below, then click an empty slot on the grid to place it.</span>
            </div>
          )}

          {/* Subjects List */}
          <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
            {semesterOfferings.length === 0 ? (
              <div className="text-center py-8 px-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-md border border-dashed border-slate-200 dark:border-slate-700 space-y-3">
                <p className="text-xs text-slate-500 font-medium">
                  No course offerings found for {activeBranch?.code} Sem {activeSemester}.
                </p>
                {activeCohort && (
                  <button
                    onClick={() => populateCurriculumMutation.mutate(activeCohort.id)}
                    disabled={populateCurriculumMutation.isPending}
                    className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white inline-flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Populate from Curriculum</span>
                  </button>
                )}
              </div>
            ) : (
              semesterOfferings.map((offering) => {
                const asgn = assignments.find((a) => a.course_offering === offering.id);
                const isSelected = activeOffering?.id === offering.id;
                const isLab = offering.course_type === 'LAB';
                const scheduledCount = scheduledCountByOffering[offering.id] || 0;
                const maxMeetings = isLab ? 2 : offering.course_credit || 3;
                const isComplete = scheduledCount >= maxMeetings;

                return (
                  <div
                    key={offering.id}
                    onClick={() => selectOfferingForPlacement(offering)}
                    className={`p-3.5 rounded-md border text-xs cursor-pointer transition-colors ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-950/40 ring-1 ring-inset ring-primary-500'
                        : isComplete
                        ? 'border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/20 opacity-70 hover:opacity-100'
                        : 'border-slate-200 dark:border-slate-800 hover:border-primary-400 bg-slate-50/40 dark:bg-slate-800/30'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          isLab
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                        }`}
                      >
                        {offering.course_type}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-semibold whitespace-nowrap ${
                          isComplete ? 'text-emerald-600' : 'text-slate-500'
                        }`}
                      >
                        {scheduledCount}/{maxMeetings} placed
                      </span>
                    </div>

                    <h3 className="font-semibold font-mono text-slate-900 dark:text-white">
                      {offering.course_code}
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 truncate font-medium">
                      {offering.course_name}
                    </p>

                    <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px]">
                      <span className="text-slate-500 truncate max-w-[140px] font-medium flex items-center gap-1">
                        <UserCheck className="w-3 h-3 text-slate-400 flex-shrink-0" />
                        <span>
                          {asgn ? (
                            asgn.professor_name
                          ) : (
                            <span className="text-rose-500 font-semibold">No Professor</span>
                          )}
                        </span>
                      </span>
                      <span className="text-slate-400 font-mono text-[10px] whitespace-nowrap flex-shrink-0">
                        {isLab ? '3 h' : '1 h'}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right 3 Columns: Interactive Master Timetable Grid */}
        <div className="min-w-0 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <span>
                  {activeBranch ? `${activeBranch.name} (${activeBranch.code})` : 'Timetable Grid'}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-primary-100 dark:bg-primary-950 text-primary-700 dark:text-primary-300 font-semibold font-mono">
                  Sem {activeSemester}
                </span>
              </h2>
              <p className="text-xs text-slate-500">
                Weekly master schedule — 8 daily slots (08:30–18:00). Click empty slot to place active subject into Room {activeRoom?.room_no}.
              </p>
            </div>

            {/* Validation Hover Indicator */}
            <div className="min-h-[30px] flex items-center">
              {hoveredSlot && activeOffering && (
                <div className="flex items-center gap-2 text-xs">
                  {isValidating ? (
                    <span className="text-slate-400 flex items-center gap-1">
                      <RefreshCw className="w-3 h-3 animate-spin" /> Validating...
                    </span>
                  ) : slotValidation?.allowed ? (
                    <span className="px-2.5 py-1 rounded font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Allowed: Room {activeRoom?.room_no}
                    </span>
                  ) : slotValidation && !slotValidation.allowed ? (
                    <span
                      className="px-2.5 py-1 rounded font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 flex items-center gap-1 truncate max-w-xs"
                      title={slotValidation.conflicts[0]?.message}
                    >
                      <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                      <span className="truncate">
                        {slotValidation.conflicts[0]?.message || 'Clash Detected'}
                      </span>
                    </span>
                  ) : null}
                </div>
              )}
            </div>
          </div>

          {/* Timetable Table Grid */}
          {!activeVersion ? (
            <div className="py-16 px-4 text-center bg-slate-50/50 dark:bg-slate-800/20 rounded-md border border-dashed border-slate-300 dark:border-slate-700">
              <RefreshCw className="w-8 h-8 text-primary-500 animate-spin mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
                Loading Timetable...
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Setting up schedule for {activeTerm?.name || 'the academic term'}.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] table-fixed border-collapse border border-slate-200 dark:border-slate-800 text-xs">
                <colgroup>
                  <col className="w-24" />
                  {WEEKDAYS.map((day) => (
                    <col key={day.id} />
                  ))}
                </colgroup>
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 font-semibold">
                    <th className="p-3 border border-slate-200 dark:border-slate-800 w-28 text-left">
                      Time Slot
                    </th>
                    {WEEKDAYS.map((day) => (
                      <th
                        key={day.id}
                        className="p-3 border border-slate-200 dark:border-slate-800 text-center font-semibold"
                      >
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
                          {/* Time Slot Column */}
                          <td className="p-2.5 border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 text-slate-500 font-mono text-[11px]">
                            <div className="font-semibold text-slate-800 dark:text-slate-200">
                              Slot {slot.no}
                            </div>
                            <div className="text-[10px] text-slate-400">{slot.time}</div>
                          </td>

                          {/* 5 Day Cells for this slot */}
                          {WEEKDAYS.map((day) => {
                            const meeting = meetingsBySlot.get(`${day.id}-${slot.no}`);
                            const isHovered =
                              hoveredSlot?.weekday === day.id && hoveredSlot?.slot_no === slot.no;

                            // Dynamic cell coloring based on hover validation state (neutral while validating)
                            let cellBg = 'bg-white dark:bg-slate-900';
                            if (isHovered && activeOffering) {
                              if (isValidating) {
                                cellBg = 'bg-primary-50/40 dark:bg-primary-950/20 ring-1 ring-inset ring-primary-400/60';
                              } else if (slotValidation?.allowed) {
                                cellBg =
                                  'bg-emerald-50 dark:bg-emerald-950/40 ring-1 ring-inset ring-emerald-500';
                              } else if (slotValidation && !slotValidation.allowed) {
                                cellBg =
                                  'bg-rose-50 dark:bg-rose-950/40 ring-1 ring-inset ring-rose-500';
                              }
                            }

                            return (
                              <td
                                key={day.id}
                                onMouseEnter={() => validateSlotHover(day.id, slot.no)}
                                onMouseLeave={handleSlotMouseLeave}
                                onClick={() => handleSlotClick(day.id, slot.no)}
                                className={`p-2 border border-slate-200 dark:border-slate-800 h-20 align-top transition-colors duration-150 cursor-pointer relative ${cellBg}`}
                              >
                                {meeting ? (
                                  <div
                                    className={`p-2 rounded-lg border text-[11px] space-y-1 h-full flex flex-col justify-between ${
                                      meeting.course_type === 'LAB'
                                        ? 'bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800/60 text-purple-950 dark:text-purple-200'
                                        : 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800/60 text-blue-950 dark:text-blue-200'
                                    }`}
                                  >
                                    <div>
                                      <div className="flex items-center justify-between gap-1 min-w-0 font-semibold">
                                        <span className="font-mono flex-shrink-0">{meeting.course_code}</span>
                                        <span className="text-[10px] px-1.5 py-0.2 rounded whitespace-nowrap truncate min-w-0 bg-white/70 dark:bg-black/40 font-semibold border border-black/5 dark:border-white/5">
                                          {meeting.room_no}
                                        </span>
                                      </div>
                                      <p className="truncate font-medium">{meeting.course_name}</p>
                                    </div>

                                    <div className="flex items-center justify-between text-[10px] opacity-80 pt-1 border-t border-black/5 dark:border-white/5">
                                      <span className="truncate">{meeting.professor_name}</span>
                                      {meeting.group_codes && meeting.group_codes.length > 0 && !meeting.group_codes.includes('ALL') && (
                                        <span className="font-mono font-semibold">
                                          [{meeting.group_codes.join(', ')}]
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                ) : isHovered && activeOffering ? (
                                  <div className="text-[11px] text-center mt-1 h-5 leading-5 overflow-hidden whitespace-nowrap text-ellipsis">
                                    {isValidating ? (
                                      <span className="text-slate-400 font-medium block">
                                        Validating...
                                      </span>
                                    ) : slotValidation?.allowed ? (
                                      <span className="text-emerald-700 dark:text-emerald-300 font-semibold block truncate">
                                        + Place in Room {activeRoom?.room_no}
                                      </span>
                                    ) : slotValidation && !slotValidation.allowed ? (
                                      <span className="text-rose-600 dark:text-rose-400 font-semibold block truncate">
                                        {slotValidation?.conflicts[0]?.type || 'Clash'}
                                      </span>
                                    ) : null}
                                  </div>
                                ) : null}
                              </td>
                            );
                          })}
                        </tr>

                        {/* Visual Lunch Break Row */}
                        {isLunchBreakSlot && (
                          <tr className="bg-amber-50/70 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-center text-[11px] font-semibold">
                            <td className="p-2 border border-slate-200 dark:border-slate-800 font-mono whitespace-nowrap">
                              <Coffee className="w-3.5 h-3.5 inline-block align-[-2px] mr-1" />12:30–14:00
                            </td>
                            <td
                              colSpan={5}
                              className="p-2 border border-slate-200 dark:border-slate-800"
                            >
                              Mandatory University Lunch Break — No lectures or laboratory sessions permitted
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Meeting Detail Modal */}
      {isDetailModalOpen && selectedMeeting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                  Scheduled Lecture Details
                </span>
                <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                  {selectedMeeting.course_code} — {selectedMeeting.course_name}
                </h2>
              </div>
              <button
                onClick={() => setIsDetailModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Faculty Professor</span>
                <span className="font-semibold">{selectedMeeting.professor_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Day & Time</span>
                <span className="font-semibold">
                  {selectedMeeting.weekday_display} (Slots {selectedMeeting.start_slot} to{' '}
                  {selectedMeeting.end_slot})
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Duration</span>
                <span className="font-semibold">{selectedMeeting.duration_slots} Hour(s)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Current Room</span>
                <span className="font-semibold font-mono">
                  Room {selectedMeeting.room_no} ({selectedMeeting.building_code})
                </span>
              </div>
              {selectedMeeting.group_codes && selectedMeeting.group_codes.length > 0 && (
                <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Target Student Group</span>
                  <span className="font-semibold font-mono text-primary-600">
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

      {/* Phase 5 Auto-Scheduler Modals */}
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
