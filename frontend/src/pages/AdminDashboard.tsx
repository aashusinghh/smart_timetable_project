import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Building2,
  GitBranch,
  FileCode2,
  Users,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  DoorOpen,
  Calendar,
  BookOpen,
  UserCheck,
  FileSpreadsheet,
  ShieldCheck,
  FileText,
  Coffee,
} from 'lucide-react';
import { academicsService } from '../services/academics';
import { facilitiesService } from '../services/facilities';
import { facultyService } from '../services/faculty';
import { useAuth } from '../hooks/useAuth';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: academicsService.getDepartments,
  });

  const { data: branches = [] } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  const { data: rooms = [] } = useQuery({
    queryKey: ['rooms'],
    queryFn: () => facilitiesService.getRooms(),
  });

  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: () => academicsService.getCourses(),
  });

  const { data: cohorts = [] } = useQuery({
    queryKey: ['cohorts'],
    queryFn: () => academicsService.getCohorts(),
  });

  const { data: professors = [] } = useQuery({
    queryKey: ['professors'],
    queryFn: () => facultyService.getProfessors(),
  });

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-primary-600 via-indigo-600 to-indigo-700 p-6 md:p-8 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-sm text-white mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Phase 4 — Real-Time Updates, Publication & Faculty Portals</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
              Welcome, {user?.full_name || 'Administrator'}
            </h1>
            <p className="mt-1 text-sm text-primary-100 max-w-xl">
              University timetable master administration portal. Review draft schedules, perform full clash sweeps, publish live schedules, and inspect audit logs.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              to="/schedule-review"
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-white text-primary-700 hover:bg-primary-50 shadow-sm transition-colors flex items-center gap-1.5"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-primary-600" />
              <span>Review & Publish</span>
            </Link>
            <Link
              to="/timetable"
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-primary-500/30 hover:bg-primary-500/50 text-white border border-white/20 backdrop-blur-sm transition-colors flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Timetable Planner</span>
            </Link>
            <Link
              to="/audit-logs"
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-primary-500/30 hover:bg-primary-500/50 text-white border border-white/20 backdrop-blur-sm transition-colors flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Audit Trail</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Departments & Branches
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <Building2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {departments.length} / {branches.length}
            </span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Depts / Active Branches</p>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Campus Rooms & Labs
            </span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center">
              <DoorOpen className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {rooms.length}
            </span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Total classrooms & labs</p>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Courses in Catalog
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {courses.length}
            </span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Theory & lab courses</p>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Faculty Members
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <UserCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {professors.length}
            </span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Professors with profiles</p>
          </div>
        </div>
      </div>

      {/* Phase 4 Timetable Operations */}
      <div>
        <h2 className="text-base font-bold text-slate-900 dark:text-white mb-4">
          Phase 4 Schedule Operations & Publication
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <Link
            to="/schedule-review"
            className="p-5 rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50/50 dark:from-emerald-950/40 dark:to-teal-950/20 border-2 border-emerald-500 hover:border-emerald-600 transition-all shadow-sm group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <ArrowRight className="w-4 h-4 text-emerald-500 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="font-bold text-sm text-emerald-950 dark:text-emerald-100">Schedule Review</h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
              Inspect submitted schedules, run 5-rule collision sweep, and publish live versions.
            </p>
          </Link>

          <Link
            to="/timetable"
            className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-primary-500 transition-all shadow-sm group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-primary-50 dark:bg-primary-950/60 text-primary-600 flex items-center justify-center">
                <Calendar className="w-5 h-5" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">Timetable Planner</h3>
            <p className="text-xs text-slate-500 mt-1">
              Interactive 8-slot weekly grid with live WebSocket synchronization & reservation locking.
            </p>
          </Link>

          <Link
            to="/audit-logs"
            className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-rose-500 transition-all shadow-sm group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-950/60 text-rose-600 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-rose-600 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">Audit Trail Logs</h3>
            <p className="text-xs text-slate-500 mt-1">
              Track who scheduled, moved, deleted, reviewed, or published every timetable meeting.
            </p>
          </Link>

          <Link
            to="/holidays"
            className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-500 transition-all shadow-sm group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 flex items-center justify-center">
                <Coffee className="w-5 h-5" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">Holidays & Overrides</h3>
            <p className="text-xs text-slate-500 mt-1">
              Define academic calendar holidays and swap timetable day schedules for specific dates.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
};
