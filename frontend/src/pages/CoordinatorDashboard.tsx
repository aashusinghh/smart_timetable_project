import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  Calendar,
  GitBranch,
  Clock,
  AlertCircle,
  FileSpreadsheet,
  Layers,
  Users,
  BookOpen,
  UserCheck,
  ArrowRight,
  Coffee,
  CheckCircle2,
} from 'lucide-react';

export const CoordinatorDashboard: React.FC = () => {
  const { user } = useAuth();

  // Find coordinator branch assignment if any
  const coordinatorAssignment = user?.role_assignments?.find(
    (a) => a.role?.code === 'BRANCH_COORDINATOR' && a.branch
  );

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-6 text-slate-900 dark:text-slate-100">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 mb-3">
              <GitBranch className="w-3.5 h-3.5" />
              <span>Branch coordinator</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              Welcome, {user?.full_name || 'Coordinator'}
            </h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 max-w-xl">
              Coordinate weekly branch timetables with real-time sync, submit draft schedules for dean review, configure cohorts, and assign faculty.
            </p>

            {coordinatorAssignment?.branch && (
              <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-mono text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                <span>Assigned Branch:</span>
                <strong>{coordinatorAssignment.branch.name} ({coordinatorAssignment.branch.code})</strong>
                <span>— {coordinatorAssignment.branch.degree_name}</span>
              </div>
            )}
          </div>

          <div className="flex-shrink-0 flex flex-wrap items-center gap-2">
            <Link
              to="/timetable"
              className="px-4 py-2.5 rounded-md bg-white text-amber-900 font-semibold text-xs hover:bg-amber-50 transition-colors flex items-center gap-2"
            >
              <Calendar className="w-4 h-4" />
              <span>Open Timetable Planner</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Grid Cards for Phase 2, 3 & 4 Workflows */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <Link
          to="/timetable"
          className="p-5 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 hover:border-amber-500 transition-colors group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-9 h-9 rounded-md border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center flex-shrink-0">
              <Calendar className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-amber-600 transition-colors" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Timetable Planner</h3>
          <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
            Weekly 8-slot interactive grid with live WebSocket sync & submit-for-review workflow.
          </p>
        </Link>

        <Link
          to="/branches/timetable"
          className="p-5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-500 transition-colors group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-9 h-9 rounded-md border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center flex-shrink-0">
              <GitBranch className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 transition-colors" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Branch Schedules</h3>
          <p className="text-xs text-slate-500 mt-1">
            View public published timetables for all cohorts and semesters across campus.
          </p>
        </Link>

        <Link
          to="/holidays"
          className="p-5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-500 transition-colors group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-9 h-9 rounded-md border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center flex-shrink-0">
              <Coffee className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 transition-colors" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Holidays & Overrides</h3>
          <p className="text-xs text-slate-500 mt-1">
            Review academic holiday calendars and day schedule override assignments.
          </p>
        </Link>

        <Link
          to="/assignments"
          className="p-5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-amber-500 transition-colors group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-9 h-9 rounded-md border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center flex-shrink-0">
              <UserCheck className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 transition-colors" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Teaching Assignments</h3>
          <p className="text-xs text-slate-500 mt-1">
            Assign faculty professors to cohort offerings and specific lab divisions.
          </p>
        </Link>
      </div>

      {/* Info notice */}
      <div className="p-5 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-800 dark:text-amber-200 space-y-1">
          <p className="font-semibold">Coordinator Role & Workflow Guide</p>
          <p>
            When your weekly draft schedule is complete and clash-free, click <strong>"Submit for Dean Review"</strong> directly inside the Timetable Planner. During review, editing is locked until approved or returned with feedback.
          </p>
        </div>
      </div>
    </div>
  );
};
