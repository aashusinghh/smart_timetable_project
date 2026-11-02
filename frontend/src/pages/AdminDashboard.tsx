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
} from 'lucide-react';
import { academicsService } from '../services/academics';
import { useAuth } from '../hooks/useAuth';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: departments = [], isLoading: loadingDepts } = useQuery({
    queryKey: ['departments'],
    queryFn: academicsService.getDepartments,
  });

  const { data: branches = [], isLoading: loadingBranches } = useQuery({
    queryKey: ['branches'],
    queryFn: () => academicsService.getBranches(),
  });

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-primary-600 via-indigo-600 to-indigo-700 p-6 md:p-8 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-sm text-white mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Phase 1 — Foundation & Authentication</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
              Welcome, {user?.full_name || 'Administrator'}
            </h1>
            <p className="mt-1 text-sm text-primary-100 max-w-xl">
              University timetable master administration portal. Manage departments, branches, academic structures, and role permissions.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/departments"
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-white text-primary-700 hover:bg-primary-50 shadow-sm transition-colors"
            >
              Add Department
            </Link>
            <Link
              to="/branches"
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-primary-500/30 hover:bg-primary-500/50 text-white border border-white/20 backdrop-blur-sm transition-colors"
            >
              Configure Branches
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Departments
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <Building2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loadingDepts ? '...' : departments.length}
            </span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Configured departments</p>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Active Branches
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <GitBranch className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loadingBranches ? '...' : branches.length}
            </span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Programs & degrees</p>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Roles Active
            </span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">3</span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Admin, Coord, Professor</p>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              API Specs
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
              <FileCode2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">OpenAPI 3</span>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">drf-spectacular online</p>
          </div>
        </div>
      </div>

      {/* Two-Column Quick Access & Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Management Links */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">University Master Data</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              to="/departments"
              className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-primary-500 dark:hover:border-primary-500 shadow-sm transition-all group"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-950/70 text-primary-600 dark:text-primary-400 flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-colors" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Department Management</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Create and organize academic departments (e.g. CSE, Computer Applications, ECE).
              </p>
            </Link>

            <Link
              to="/branches"
              className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-primary-500 dark:hover:border-primary-500 shadow-sm transition-all group"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <GitBranch className="w-5 h-5" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 transition-colors" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Branch & Degree Catalog</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Configure programs (B.Tech 8 semesters, MCA 6 semesters, M.Tech 4 semesters).
              </p>
            </Link>
          </div>

          <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex items-start gap-4">
            <div className="w-9 h-9 rounded-lg bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5">
              <FileCode2 className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white">Interactive API Documentation</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                The backend exposes full OpenAPI 3 schemas and interactive Swagger UI. Test endpoints directly with JWT bearer token.
              </p>
              <a
                href="/api/docs/"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 mt-2.5 text-xs font-semibold text-primary-600 dark:text-primary-400 hover:underline"
              >
                <span>Launch Swagger UI</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>

        {/* Phase 1 Verification Checklist Panel */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white mb-3">
            Phase 1 Deliverables
          </h2>
          <div className="space-y-3">
            {[
              { title: 'Django Project & MySQL Settings', desc: 'Custom settings split, utf8mb4, InnoDB' },
              { title: 'Custom User & Roles Model', desc: 'SUPER_ADMIN, COORDINATOR, PROFESSOR' },
              { title: 'JWT Authentication API', desc: 'POST /api/auth/login, /logout, /me' },
              { title: 'Role Permissions Enforced', desc: 'IsSuperAdmin, IsBranchCoordinator, IsProfessor' },
              { title: 'Departments & Branches API', desc: 'CRUD endpoints with Admin-only write access' },
              { title: 'Vite + React + Tailwind Frontend', desc: 'Role-conditional navigation & dashboards' },
              { title: 'Dark Mode Persistence', desc: 'Persisted in localStorage with Tailwind class' },
            ].map((item, idx) => (
              <div key={idx} className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">{item.title}</p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

