import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  GitBranch,
  Calendar,
  Clock,
  BookOpen,
  FileCode2,
  GraduationCap,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  if (!user) return null;

  const isSuperAdmin = user.is_superuser || user.roles.includes('SUPER_ADMIN');
  const isCoordinator = user.roles.includes('BRANCH_COORDINATOR');
  const isProfessor = user.roles.includes('PROFESSOR');

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-primary-600 text-white shadow-sm'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800'
    }`;

  return (
    <aside className="w-64 flex-shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col min-h-screen">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-200 dark:border-slate-800">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-500 flex items-center justify-center text-white shadow">
          <GraduationCap className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white leading-tight">
            Smart Timetable
          </h1>
          <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">University Portal</p>
        </div>
      </div>

      {/* Nav List */}
      <div className="flex-1 px-4 py-5 space-y-6 overflow-y-auto">
        {/* Dashboards Section */}
        <div>
          <p className="px-3 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
            Navigation
          </p>
          <nav className="space-y-1">
            {isSuperAdmin && (
              <NavLink to="/dashboard/admin" className={navLinkClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Admin Overview</span>
              </NavLink>
            )}

            {isCoordinator && (
              <NavLink to="/dashboard/coordinator" className={navLinkClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Coordinator Desk</span>
              </NavLink>
            )}

            {isProfessor && (
              <NavLink to="/dashboard/professor" className={navLinkClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Faculty Portal</span>
              </NavLink>
            )}
          </nav>
        </div>

        {/* Administration Section (Super Admin only) */}
        {isSuperAdmin && (
          <div>
            <p className="px-3 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
              University Setup
            </p>
            <nav className="space-y-1">
              <NavLink to="/departments" className={navLinkClass}>
                <Building2 className="w-4 h-4" />
                <span>Departments</span>
              </NavLink>
              <NavLink to="/branches" className={navLinkClass}>
                <GitBranch className="w-4 h-4" />
                <span>Branches & Degrees</span>
              </NavLink>
            </nav>
          </div>
        )}

        {/* System & API docs */}
        <div>
          <p className="px-3 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
            System & Tools
          </p>
          <nav className="space-y-1">
            <a
              href="/api/docs/"
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <FileCode2 className="w-4 h-4 text-emerald-500" />
                <span>Swagger API Docs</span>
              </div>
              <span className="text-[10px] bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 font-semibold px-1.5 py-0.5 rounded">
                v1
              </span>
            </a>
          </nav>
        </div>
      </div>

      {/* Role Badge in Sidebar Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-950 flex items-center justify-center text-primary-600 dark:text-primary-400 font-bold text-xs">
            {user.full_name?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
              {user.full_name}
            </p>
            <div className="flex items-center gap-1 mt-0.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">
                {user.roles.join(', ') || 'USER'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

