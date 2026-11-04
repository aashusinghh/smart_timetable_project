import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { UserCheck, BookOpen, Calendar, Clock, Award, Building, ArrowRight, Printer, GitBranch } from 'lucide-react';

export const ProfessorDashboard: React.FC = () => {
  const { user } = useAuth();
  const profile = user?.professor_profile;

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-700 p-6 md:p-8 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-sm text-white mb-3">
              <Award className="w-3.5 h-3.5" />
              <span>Faculty Member Portal — Phase 4 Live</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
              Welcome, {user?.full_name || 'Professor'}
            </h1>
            <p className="mt-1 text-sm text-emerald-100 max-w-xl">
              View your published weekly teaching schedule, room allocations, batch divisions, and campus holidays.
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

          <div className="flex-shrink-0 flex flex-wrap items-center gap-2">
            <Link
              to="/my-timetable"
              className="px-4 py-2.5 rounded-xl bg-white text-emerald-900 font-bold text-xs hover:bg-emerald-50 shadow-md transition-all flex items-center gap-2"
            >
              <Calendar className="w-4 h-4 text-emerald-600" />
              <span>View My Timetable</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Action & Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Link
          to="/my-timetable"
          className="p-5 rounded-xl bg-white dark:bg-slate-900 border-2 border-emerald-500/50 hover:border-emerald-500 transition-all shadow-sm group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-emerald-600 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Personal Teaching Schedule</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Weekly interactive schedule with room numbers, batch division indicators, and one-click print layout.
          </p>
        </Link>

        <Link
          to="/branches/timetable"
          className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-emerald-500 transition-all shadow-sm group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <GitBranch className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Branch Timetables</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Explore published timetables for all departments, branches, and semesters across the university.
          </p>
        </Link>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Clash-Free Assurance</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Zero double-booking guarantee</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Database reservation locks ensure you are never assigned to two cohorts or rooms at the same time.
          </p>
        </div>
      </div>
    </div>
  );
};
