import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { Calendar, GitBranch, Clock, AlertCircle, FileSpreadsheet, Layers } from 'lucide-react';

export const CoordinatorDashboard: React.FC = () => {
  const { user } = useAuth();

  // Find coordinator branch assignment if any
  const coordinatorAssignment = user?.role_assignments?.find(
    (a) => a.role?.code === 'BRANCH_COORDINATOR' && a.branch
  );

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-amber-600 to-orange-600 p-6 md:p-8 text-white shadow-sm">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-sm text-white mb-3">
          <GitBranch className="w-3.5 h-3.5" />
          <span>Branch Coordinator Portal</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          Welcome, {user?.full_name || 'Coordinator'}
        </h1>
        <p className="mt-1 text-sm text-amber-100 max-w-xl">
          Coordinate timetables, monitor cohort allocations, and plan conflict-free schedules for your assigned branch.
        </p>

        {coordinatorAssignment?.branch && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/20 text-xs font-mono text-white backdrop-blur-sm border border-white/20">
            <span>Assigned Branch:</span>
            <strong>{coordinatorAssignment.branch.name} ({coordinatorAssignment.branch.code})</strong>
            <span>— {coordinatorAssignment.branch.degree_name}</span>
          </div>
        )}
      </div>

      {/* Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Active Draft Schedule</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Term 2026-27 (Odd)</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Schedule drafting is prepared in Phase 3 (Timetable Grid & Conflict Validation).
          </p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Cohorts & Sections</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Sections A, B</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Lab groups and cohort structures will be populated in Phase 2 (Academic Data Setup).
          </p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">8 Daily Time Slots</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">08:30 – 18:00 (Lunch excluded)</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Enforces strict 2-credit lab (2×3h) and 3/4-credit lecture delivery patterns.
          </p>
        </div>
      </div>

      {/* Info notice */}
      <div className="p-5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-800 dark:text-amber-200 space-y-1">
          <p className="font-semibold">Coordinator Role Privileges Active</p>
          <p>
            As a Branch Coordinator, your timetable access is scoped strictly to your assigned branch. You will be able to place meetings and receive immediate conflict alerts when professors are booked by other branches.
          </p>
        </div>
      </div>
    </div>
  );
};

