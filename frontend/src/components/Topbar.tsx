import React from 'react';
import { Sun, Moon, LogOut, ShieldCheck, UserCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';

export const Topbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();

  if (!user) return null;

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Role Info */}
      <div className="flex items-center gap-3">
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 dark:bg-primary-950/70 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800/60">
          <ShieldCheck className="w-3.5 h-3.5" />
          {user.roles.includes('SUPER_ADMIN') || user.is_superuser
            ? 'Super Administrator'
            : user.roles.includes('BRANCH_COORDINATOR')
            ? 'Branch Coordinator'
            : 'Faculty / Professor'}
        </span>
        {user.employee_code && (
          <span className="hidden sm:inline-block text-xs text-slate-500 dark:text-slate-400">
            ID: <span className="font-mono">{user.employee_code}</span>
          </span>
        )}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Dark Mode Toggle */}
        <button
          onClick={toggleTheme}
          aria-label="Toggle dark mode"
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
        </button>

        {/* User Info */}
        <div className="hidden md:flex flex-col text-right">
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-tight">
            {user.full_name}
          </span>
          <span className="text-xs text-slate-400 dark:text-slate-500 truncate max-w-[200px]">
            {user.email}
          </span>
        </div>

        <div className="h-5 w-px bg-slate-200 dark:bg-slate-800 mx-1" />

        {/* Logout Button */}
        <button
          onClick={() => logout()}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/50 border border-rose-200 dark:border-rose-900/50 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};

