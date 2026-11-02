import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { UserCheck, BookOpen, Calendar, Clock, Award, Building } from 'lucide-react';

export const ProfessorDashboard: React.FC = () => {
  const { user } = useAuth();
  const profile = user?.professor_profile;

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-700 p-6 md:p-8 text-white shadow-sm">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-sm text-white mb-3">
          <Award className="w-3.5 h-3.5" />
          <span>Faculty Member Portal</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          Welcome, {user?.full_name || 'Professor'}
        </h1>
        <p className="mt-1 text-sm text-emerald-100 max-w-xl">
          View your daily teaching schedule, course allocations, and classroom assignments across university branches.
        </p>

        {profile && (
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs">
            <span className="px-3 py-1.5 rounded-lg bg-black/20 text-white backdrop-blur-sm border border-white/20 font-medium">
              {profile.designation}
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-black/20 text-white backdrop-blur-sm border border-white/20 font-medium">
              Department: {profile.department.name} ({profile.department.code})
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-black/20 text-white backdrop-blur-sm border border-white/20 font-medium">
              Max Load: {profile.max_hours_per_day} hrs/day
            </span>
          </div>
        )}
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Personal Timetable</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Weekly schedule grid</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Read-only timetable view with room numbers and batch information will be unlocked in Phase 4.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Assigned Courses</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Theory & Lab Mappings</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Teaching assignments are fixed per university curriculum in Phase 2.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Conflict Protection</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Zero double-booking guarantee</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Atomic database reservation rows prevent overlapping slots across all branches.
          </p>
        </div>
      </div>
    </div>
  );
};

