import React, { useState, useMemo, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import {
  Calendar,
  CalendarRange,
  Building2,
  GraduationCap,
  Layers,
  Printer,
  Coffee,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  RefreshCw,
  Lock,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { timetableService } from '../services/timetable';
import { academicsService } from '../services/academics';
import { ScheduledMeeting } from '../types';
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
  { no: 5, time: '14:00 - 15:00', session: 'AFTERNOON' },
  { no: 6, time: '15:00 - 16:00', session: 'AFTERNOON' },
  { no: 7, time: '16:00 - 17:00', session: 'AFTERNOON' },
  { no: 8, time: '17:00 - 18:00', session: 'AFTERNOON' },
];

export const BranchTimetablePage: React.FC = () => {
  const { id: paramBranchId } = useParams<{ id: string }>();
  const { user } = useAuth();

  const isCoordinator =
    !user?.is_superuser &&
    !user?.roles?.includes('SUPER_ADMIN') &&
    user?.roles?.includes('BRANCH_COORDINATOR');

  const coordinatorAssignments = useMemo(() => {
    return (
      user?.role_assignments?.filter(
        (a) => a.role?.code === 'BRANCH_COORDINATOR' && a.branch
      ) || []
    );
  }, [user]);

  const coordinatorBranchIds = useMemo(() => {
    return coordinatorAssignments.map((a) => a.branch!.id);
  }, [coordinatorAssignments]);

  // -------------------------------------------------------------
  // 1. Academic Years Query
  // -------------------------------------------------------------
  const { data: academicYears = [] } = useQuery({
    queryKey: ['academic-years'],
    queryFn: () => academicsService.getAcademicYears(),
  });

  const [selectedYearId, setSelectedYearId] = useState<number | undefined>();

  const activeAcademicYear =
    academicYears.find((y) => y.id === selectedYearId) ||
    academicYears.find((y) => y.is_current) ||
    academicYears[0];

  // -------------------------------------------------------------
  // 2. Academic Terms Query & Odd/Even Semester Cycle
  // -------------------------------------------------------------
  const { data: allTerms = [] } = useQuery({
    queryKey: ['academic-terms'],
    queryFn: () => academicsService.getAcademicTerms(),
  });

  const [termCycle, setTermCycle] = useState<'ODD' | 'EVEN'>('ODD');
  const [selectedTermId, setSelectedTermId] = useState<number | undefined>();

  // Terms strictly filtered by active academic year
  const terms = useMemo(() => {
    if (!activeAcademicYear) return allTerms;
    const filtered = allTerms.filter((t) => t.academic_year === activeAcademicYear.id);
    return filtered.length > 0 ? filtered : allTerms;
  }, [allTerms, activeAcademicYear]);

  const activeTerm =
    terms.find((t) => t.id === selectedTermId) ||
    terms.find((t) => t.term_type === termCycle) ||
    pickCurrentTerm(terms) ||
    terms[0];

  // Sync selectedTermId when active year or cycle changes
  useEffect(() => {
    if (terms.length > 0) {
      const match = terms.find((t) => t.id === selectedTermId) ||
                    terms.find((t) => t.term_type === termCycle) ||
                    terms[0];
      if (match && match.id !== selectedTermId) {
        setSelectedTermId(match.id);
      }
    }
  }, [terms, termCycle, selectedTermId]);

  // Sync termCycle when activeTerm type changes
  useEffect(() => {
    if (activeTerm?.term_type === 'ODD' || activeTerm?.term_type === 'EVEN') {
      setTermCycle(activeTerm.term_type);
    }
  }, [activeTerm?.term_type]);

  // -------------------------------------------------------------
  // 3. Departments Query
  // -------------------------------------------------------------
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: () => academicsService.getDepartments(),
  });

  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | undefined>();

  // -------------------------------------------------------------
  // 4. Branches Query & Strict Department Hierarchy
  // -------------------------------------------------------------
  const { data: branches = [] } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  // Allowed branches based on role (Coordinators are strictly restricted to their assigned branch)
  const allowedBranches = useMemo(() => {
    if (!isCoordinator || coordinatorBranchIds.length === 0) {
      return branches;
    }
    return branches.filter((b) => coordinatorBranchIds.includes(b.id));
  }, [branches, isCoordinator, coordinatorBranchIds]);

  // Allowed departments based on allowedBranches
  const allowedDepartments = useMemo(() => {
    if (!isCoordinator || coordinatorBranchIds.length === 0) {
      return departments;
    }
    const deptIds = new Set(allowedBranches.map((b) => b.department));
    return departments.filter((d) => deptIds.has(d.id));
  }, [departments, allowedBranches, isCoordinator, coordinatorBranchIds]);

  // If URL parameter contains branch ID, auto-select it and its department (if allowed)
  useEffect(() => {
    if (paramBranchId && allowedBranches.length > 0) {
      const bId = Number(paramBranchId);
      const b = allowedBranches.find((item) => item.id === bId);
      if (b) {
        setSelectedBranchId(b.id);
        if (b.department) {
          setSelectedDepartmentId(b.department);
        }
      }
    }
  }, [paramBranchId, allowedBranches]);

  const activeDepartment =
    allowedDepartments.find((d) => d.id === selectedDepartmentId) ||
    allowedDepartments[0] ||
    departments[0];

  // Branches strictly belonging to the active department AND allowed branches
  const departmentBranches = useMemo(() => {
    if (!activeDepartment) return allowedBranches;
    return allowedBranches.filter((b) => b.department === activeDepartment.id);
  }, [allowedBranches, activeDepartment]);

  const [selectedBranchId, setSelectedBranchId] = useState<number | undefined>(
    paramBranchId ? Number(paramBranchId) : undefined
  );

  const activeBranch =
    departmentBranches.find((b) => b.id === selectedBranchId) || departmentBranches[0] || null;

  // Synchronize selectedBranchId and selectedDepartmentId for coordinators
  useEffect(() => {
    if (isCoordinator && allowedBranches.length > 0) {
      if (!selectedBranchId || !allowedBranches.some((b) => b.id === selectedBranchId)) {
        const first = allowedBranches[0];
        setSelectedBranchId(first.id);
        if (first.department) {
          setSelectedDepartmentId(first.department);
        }
      }
    } else if (departmentBranches.length > 0) {
      if (!selectedBranchId || !departmentBranches.some((b) => b.id === selectedBranchId)) {
        setSelectedBranchId(departmentBranches[0].id);
      }
    } else {
      setSelectedBranchId(undefined);
    }
  }, [isCoordinator, allowedBranches, departmentBranches, selectedBranchId]);

  // -------------------------------------------------------------
  // 5. Semesters
  // -------------------------------------------------------------
  const maxSemesters = activeBranch ? (activeBranch.max_semesters || 8) : 0;
  const allSemesters = useMemo(() => Array.from({ length: maxSemesters }, (_, i) => i + 1), [maxSemesters]);

  const visibleSemesters = useMemo(() => {
    if (termCycle === 'ODD') return allSemesters.filter((s) => s % 2 === 1);
    if (termCycle === 'EVEN') return allSemesters.filter((s) => s % 2 === 0);
    return allSemesters;
  }, [allSemesters, termCycle]);

  const [selectedSemester, setSelectedSemester] = useState<number | undefined>(1);

  const activeSemester =
    selectedSemester !== undefined && visibleSemesters.includes(selectedSemester)
      ? selectedSemester
      : visibleSemesters[0] || (visibleSemesters.length > 0 ? 1 : undefined);

  useEffect(() => {
    if (visibleSemesters.length > 0 && (!selectedSemester || !visibleSemesters.includes(selectedSemester))) {
      setSelectedSemester(visibleSemesters[0]);
    }
  }, [visibleSemesters, selectedSemester]);

  // -------------------------------------------------------------
  // 6. Cohorts (Sections) for Branch and Semester
  // -------------------------------------------------------------
  const { data: allCohorts = [] } = useQuery({
    queryKey: ['cohorts', activeTerm?.id],
    queryFn: () => academicsService.getCohorts({ term: activeTerm?.id }),
    enabled: !!activeTerm,
  });

  const matchingCohorts = useMemo(() => {
    if (!activeBranch) return [];
    return allCohorts.filter(
      (c) => c.branch === activeBranch.id && (activeSemester !== undefined ? c.semester_no === activeSemester : true)
    );
  }, [allCohorts, activeBranch, activeSemester]);

  const [selectedCohortId, setSelectedCohortId] = useState<number | undefined>();
  const activeCohort = matchingCohorts.find((c) => c.id === selectedCohortId);

  // -------------------------------------------------------------
  // 7. Branch Timetable Query (Strictly Published Only)
  // -------------------------------------------------------------
  const { data: branchTimetable, isLoading, isFetching } = useQuery({
    queryKey: ['branch-timetable', activeBranch?.id, activeTerm?.id, activeSemester, activeCohort?.id],
    placeholderData: keepPreviousData,
    queryFn: () =>
      activeBranch && activeTerm
        ? timetableService.getBranchTimetable(activeBranch.id, {
            term_id: activeTerm.id,
            semester_no: activeSemester,
            cohort_id: activeCohort?.id,
            published_only: true,
          })
        : Promise.resolve({
            branch_id: 0,
            branch_code: '',
            branch_name: '',
            schedule_version_id: null,
            schedule_status: null,
            is_published: false,
            version_name: null,
            meetings: [],
          }),
    enabled: !!activeBranch && !!activeTerm,
  });

  // Map meetings by weekday and slot
  const meetingsMap = useMemo(() => {
    const map = new Map<string, ScheduledMeeting>();
    if (!branchTimetable?.meetings) return map;
    branchTimetable.meetings.forEach((m) => {
      for (let s = m.start_slot; s <= m.end_slot; s++) {
        map.set(`${m.weekday}-${s}`, m);
      }
    });
    return map;
  }, [branchTimetable]);

  const isSchedulePublished = Boolean(branchTimetable?.is_published);

  return (
    <div className="space-y-5 print:space-y-3">
      {/* ---------------------------------------------------------- */}
      {/* Screen Header */}
      {/* ---------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-primary-600" />
            <span>Branch Academic Schedule</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Published institutional timetable for students, faculty, and academic administration.
          </p>
          {isCoordinator && allowedBranches.length > 0 && (
            <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 text-[11px] border border-amber-200 dark:border-amber-800/60 font-medium">
              <Lock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>Branch Coordinator Access: Restricted to {allowedBranches.map((b) => `${b.name} (${b.code})`).join(', ')}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            disabled={!isSchedulePublished || isLoading}
            className={`px-3.5 py-2 text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-xs transition-colors ${
              isSchedulePublished
                ? 'bg-primary-600 hover:bg-primary-700 text-white cursor-pointer'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
            }`}
            title={isSchedulePublished ? 'Print this official timetable' : 'Printing is only available for published timetables'}
          >
            <Printer className="w-4 h-4" />
            <span>Print Schedule</span>
          </button>
        </div>
      </div>

      {/* ---------------------------------------------------------- */}
      {/* Selection Control Panel: Year -> Department -> Course -> Semester */}
      {/* ---------------------------------------------------------- */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-xs print:hidden space-y-3.5">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2.5">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <CalendarRange className="w-4 h-4 text-primary-600" />
            <span>Academic Schedule Explorer</span>
          </span>
          <span className="text-[11px] text-slate-400">
            Selection Workflow: Academic Year → Department → Course / Degree → Semester
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* 1. Academic Year & Term Cycle */}
          <div>
            <div className="flex items-center justify-between h-5 mb-1.5">
              <label className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                <Calendar className="w-3.5 h-3.5 text-primary-600" />
                <span>Academic Year</span>
              </label>
              <div className="inline-flex h-5 items-center rounded-md p-px bg-slate-100 dark:bg-slate-800 text-[10px] leading-none font-semibold border border-slate-200 dark:border-slate-700">
                <button
                  type="button"
                  onClick={() => setTermCycle('ODD')}
                  className={`px-2 py-[3px] rounded transition-colors ${
                    termCycle === 'ODD'
                      ? 'bg-amber-500 text-white'
                      : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                  }`}
                  title="Odd Semesters"
                >
                  Odd
                </button>
                <button
                  type="button"
                  onClick={() => setTermCycle('EVEN')}
                  className={`px-2 py-[3px] rounded transition-colors ${
                    termCycle === 'EVEN'
                      ? 'bg-amber-500 text-white'
                      : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                  }`}
                  title="Even Semesters"
                >
                  Even
                </button>
              </div>
            </div>
            <select
              value={activeAcademicYear?.id || ''}
              onChange={(e) => {
                const yId = Number(e.target.value);
                setSelectedYearId(yId);
              }}
              className="w-full px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none"
            >
              {academicYears.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.name} {y.is_current ? '(Current Academic Year)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* 2. Department */}
          <div>
            <label className="flex items-center gap-1.5 h-5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              <Building2 className="w-3.5 h-3.5 text-indigo-600" />
              <span>Department</span>
              {isCoordinator && allowedDepartments.length <= 1 && (
                <Lock className="w-3 h-3 text-slate-400 ml-auto" />
              )}
            </label>
            <select
              value={activeDepartment?.id || ''}
              disabled={isCoordinator && allowedDepartments.length <= 1}
              onChange={(e) => {
                const newDeptId = Number(e.target.value);
                setSelectedDepartmentId(newDeptId);
                const deptBranches = allowedBranches.filter((b) => b.department === newDeptId);
                setSelectedBranchId(deptBranches[0]?.id || undefined);
                setSelectedCohortId(undefined);
              }}
              className="w-full px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none disabled:opacity-75 disabled:cursor-not-allowed"
            >
              {allowedDepartments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          {/* 3. Course / Degree Program */}
          <div>
            <label className="flex items-center gap-1.5 h-5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              <GraduationCap className="w-3.5 h-3.5 text-purple-600" />
              <span>Course / Degree Program</span>
              {isCoordinator && departmentBranches.length <= 1 && (
                <Lock className="w-3 h-3 text-slate-400 ml-auto" />
              )}
            </label>
            <select
              value={activeBranch?.id || ''}
              disabled={departmentBranches.length === 0 || (isCoordinator && departmentBranches.length <= 1)}
              onChange={(e) => {
                setSelectedBranchId(Number(e.target.value));
                setSelectedCohortId(undefined);
              }}
              className="w-full px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none disabled:opacity-75 disabled:cursor-not-allowed"
            >
              {departmentBranches.length === 0 ? (
                <option value="">No degree programs available</option>
              ) : (
                departmentBranches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.code}) — {b.degree_name}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* 4. Semester & Section */}
          <div>
            <div className="flex items-center justify-between h-5 mb-1.5">
              <label className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                <Layers className="w-3.5 h-3.5 text-amber-600" />
                <span>Semester</span>
              </label>
              {matchingCohorts.length > 1 && (
                <span className="text-[10px] text-slate-400">
                  {matchingCohorts.length} sections
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <select
                value={activeSemester || ''}
                onChange={(e) => {
                  setSelectedSemester(Number(e.target.value));
                  setSelectedCohortId(undefined);
                }}
                disabled={visibleSemesters.length === 0}
                className="w-full px-3 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none disabled:opacity-50"
              >
                {visibleSemesters.length === 0 ? (
                  <option value="">No semesters available</option>
                ) : (
                  visibleSemesters.map((s) => (
                    <option key={s} value={s}>
                      Semester {s} ({s % 2 === 1 ? 'Odd' : 'Even'})
                    </option>
                  ))
                )}
              </select>

              {matchingCohorts.length > 1 && (
                <select
                  value={selectedCohortId || ''}
                  onChange={(e) => setSelectedCohortId(e.target.value ? Number(e.target.value) : undefined)}
                  className="px-2 py-2 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-semibold focus:ring-1 focus:ring-primary-500 focus:outline-none shrink-0"
                >
                  <option value="">All Sections</option>
                  {matchingCohorts.map((c) => (
                    <option key={c.id} value={c.id}>
                      Sec {c.section_code}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
        </div>

        {/* Active Selection Summary Pill */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px]">
          <div className="text-slate-500 font-medium flex items-center gap-2">
            <span>Viewing:</span>
            <span className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 font-mono font-semibold text-slate-800 dark:text-slate-200">
              {activeAcademicYear?.name || 'Academic Year'} • {activeDepartment?.code} • {activeBranch?.code || 'No Branch'} • {activeSemester !== undefined ? `Sem ${activeSemester}` : 'No Sem'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {isSchedulePublished ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Officially Published</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                <span>Not Published Yet</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------------- */}
      {/* Printable Masthead (Visible ONLY in Print Mode) */}
      {/* ---------------------------------------------------------- */}
      <div className="hidden print:block mb-4 border-b-2 border-black pb-3 bg-white text-black">
        <div className="flex items-start justify-between pb-2 border-b border-black">
          <div>
            <h1 className="text-xl font-black tracking-tight text-black uppercase">
              National Institute of Technology Jamshedpur
            </h1>
            <p className="text-[11px] font-bold text-slate-800 uppercase tracking-wider">
              Office of the Dean Academic Affairs • Official Academic Timetable
            </p>
          </div>
          <div className="text-right text-[10px] text-black font-mono">
            <span className="inline-block px-2 py-0.5 border border-black font-bold uppercase text-black bg-white rounded">
              Status: Official Published
            </span>
            <p className="mt-1 text-slate-700">Printed: {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
          </div>
        </div>
        <div className="mt-2.5 grid grid-cols-4 gap-2 text-xs font-semibold bg-white p-2.5 rounded border-2 border-black text-black">
          <div><span className="font-bold text-slate-600 block text-[10px] uppercase">Year:</span> {activeAcademicYear?.name}</div>
          <div><span className="font-bold text-slate-600 block text-[10px] uppercase">Department:</span> {activeDepartment?.name}</div>
          <div><span className="font-bold text-slate-600 block text-[10px] uppercase">Degree:</span> {activeBranch?.name} ({activeBranch?.code})</div>
          <div><span className="font-bold text-slate-600 block text-[10px] uppercase">Semester:</span> Sem {activeSemester} {selectedCohortId ? `(Sec ${activeCohort?.section_code})` : ''}</div>
        </div>
      </div>

      {/* ---------------------------------------------------------- */}
      {/* Timetable Display Area */}
      {/* ---------------------------------------------------------- */}
      {isLoading ? (
        <div className="py-20 text-center bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs">
          <RefreshCw className="w-8 h-8 text-primary-500 animate-spin mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
            Loading Academic Schedule...
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Retrieving published timetable for {activeBranch?.name || 'branch'} Semester {activeSemester}.
          </p>
        </div>
      ) : !activeBranch ? (
        <div className="py-16 px-4 text-center bg-white dark:bg-slate-900 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 shadow-xs">
          <Building2 className="w-8 h-8 text-slate-400 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
            No Degree Program Selected
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {activeDepartment
              ? `Department "${activeDepartment.name}" has no degree programs or none is selected.`
              : 'Please select a valid academic department and degree program.'}
          </p>
        </div>
      ) : !isSchedulePublished ? (
        /* Not Published Empty State */
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-dashed border-amber-300 dark:border-amber-800/60 p-12 text-center my-4 shadow-xs">
          <div className="w-12 h-12 rounded-full bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 text-amber-600 flex items-center justify-center mx-auto mb-3.5">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-1.5">
            No Published Schedule Available
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            The timetable for <span className="font-semibold text-slate-700 dark:text-slate-300">{activeAcademicYear?.name}</span> • <span className="font-semibold text-slate-700 dark:text-slate-300">{activeBranch.name} ({activeBranch.code})</span> Semester <span className="font-semibold text-slate-700 dark:text-slate-300">{activeSemester}</span> has not been officially published yet.
          </p>
          <p className="text-[11px] text-slate-400 mt-2.5">
            Only officially published schedules are viewable and printable. Timetables are released by the Dean (Academic) once scheduling and approval are finalized.
          </p>
        </div>
      ) : (
        /* Official Published Schedule Card */
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 space-y-4 shadow-xs print:p-0 print:border-none print:shadow-none">
          {/* Official Status Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3 print:hidden">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-emerald-600 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>{activeBranch.name} ({activeBranch.code})</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-primary-100 dark:bg-primary-950 text-primary-700 dark:text-primary-300 font-semibold font-mono">
                    Sem {activeSemester}
                  </span>
                  {selectedCohortId && (
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold font-mono">
                      Sec {activeCohort?.section_code}
                    </span>
                  )}
                </h2>
                <p className="text-xs text-emerald-700 dark:text-emerald-400 font-medium mt-0.5">
                  {branchTimetable?.version_name || 'Official Published Master Schedule'} • Approved by Office of the Dean (Academic)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => window.print()}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-primary-600 hover:bg-primary-700 text-white flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
              >
                <Printer className="w-4 h-4" />
                <span>Print Schedule</span>
              </button>
            </div>
          </div>

          {/* Timetable Table Grid */}
          <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800 print:border-none print:p-0">
            <table className="w-full min-w-[720px] print:min-w-full table-fixed border-collapse border border-slate-200 dark:border-slate-800 print:border-2 print:border-black text-xs print:bg-white">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/60 print:bg-white text-slate-700 dark:text-slate-300 print:text-black font-black h-10 print:h-7">
                  <th className="p-2.5 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black w-28 text-left font-black print:bg-white uppercase tracking-wider text-[11px]">
                    Time Slot
                  </th>
                  {WEEKDAYS.map((day) => (
                    <th
                      key={day.id}
                      className="p-2.5 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black text-center font-black print:bg-white uppercase tracking-wider text-[11px]"
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
                      <tr className="h-20 print:h-[48px] print:bg-white">
                        {/* Time Slot Column */}
                        <td className="p-2 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black bg-slate-50/50 dark:bg-slate-800/30 print:bg-white text-slate-500 print:text-black font-mono text-[11px] align-top">
                          <div className="font-black text-slate-800 dark:text-slate-200 print:text-black text-[11px] leading-tight">
                            Slot {slot.no}
                          </div>
                          <div className="text-[10px] text-slate-400 print:text-black font-bold mt-0.5 leading-tight">
                            {slot.time}
                          </div>
                        </td>

                        {/* 5 Day Cells for this slot */}
                        {WEEKDAYS.map((day) => {
                          const meeting = meetingsMap.get(`${day.id}-${slot.no}`);
                          return (
                            <td
                              key={day.id}
                              className="p-1.5 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black h-20 print:h-[48px] align-top bg-white dark:bg-slate-900 print:bg-white"
                            >
                              {meeting ? (
                                <div
                                  className={`p-2 print:p-1 rounded-lg border text-[11px] h-full flex flex-col justify-between overflow-hidden print:bg-white print:border-2 print:border-black ${
                                    meeting.course_type === 'LAB'
                                      ? 'bg-purple-50 dark:bg-purple-950/40 print:bg-white border-purple-200 dark:border-purple-800/60 text-purple-950 dark:text-purple-200 print:text-black'
                                      : 'bg-blue-50 dark:bg-blue-950/40 print:bg-white border-blue-200 dark:border-blue-800/60 text-blue-950 dark:text-blue-200 print:text-black'
                                  }`}
                                >
                                  <div>
                                    <div className="flex items-center justify-between gap-1 min-w-0 font-black">
                                      <span className="font-mono flex-shrink-0 font-black text-black">
                                        {meeting.course_code}
                                      </span>
                                      <span className="text-[10px] px-1.5 py-0.2 rounded whitespace-nowrap truncate min-w-0 bg-white/80 dark:bg-black/40 print:bg-white print:border print:border-black font-black text-black">
                                        Room {meeting.room_no}
                                      </span>
                                    </div>
                                    <p className="truncate font-black text-black mt-0.5 text-[10px] leading-tight">
                                      {meeting.course_name}
                                    </p>
                                  </div>

                                  <div className="pt-0.5 border-t border-black/5 dark:border-white/5 print:border-t print:border-black flex items-center justify-between text-[10px] print:text-[9px] font-black leading-none text-black">
                                    <span className="truncate font-black">{meeting.professor_name}</span>
                                    {meeting.group_codes &&
                                      meeting.group_codes.length > 0 &&
                                      !meeting.group_codes.includes('ALL') && (
                                        <span className="font-mono font-black ml-1 shrink-0 text-black">
                                          [{meeting.group_codes.join(', ')}]
                                        </span>
                                      )}
                                  </div>
                                </div>
                              ) : null}
                            </td>
                          );
                        })}
                      </tr>

                      {/* Lunch Break Row */}
                      {isLunchBreakSlot && (
                        <tr className="bg-amber-50/70 dark:bg-amber-950/30 print:bg-white text-amber-800 dark:text-amber-300 print:text-black text-center text-[11px] font-black h-7 print:h-6 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black">
                          <td className="p-1 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black font-mono font-black whitespace-nowrap print:bg-white print:text-black">
                            <Coffee className="w-3.5 h-3.5 inline-block align-[-2px] mr-1 print:hidden" />
                            12:30–14:00
                          </td>
                          <td colSpan={5} className="p-1 border border-slate-200 dark:border-slate-800 print:border-2 print:border-black print:bg-white uppercase tracking-wider text-[11px] font-black print:text-black">
                            University Lunch Break & Mid-Day Recess
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Printable Footer */}
          <div className="hidden print:flex items-center justify-between pt-3 mt-2 border-t-2 border-black text-[10px] text-black font-bold">
            <div>
              <p className="font-black text-black">Office of the Dean (Academic Affairs)</p>
              <p className="text-black font-bold">National Institute of Technology Jamshedpur</p>
            </div>
            <div className="text-right">
              <p className="font-black text-black">Head of Department</p>
              <p className="text-black font-bold">{activeDepartment?.name}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
