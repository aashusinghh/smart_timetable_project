import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, getDashboardForUser } from '../hooks/useAuth';
import { RoleCode } from '../types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: RoleCode[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Loading university portal...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const hasPermission = user.is_superuser || allowedRoles.some((role) => user.roles.includes(role));
    if (!hasPermission) {
      // Redirect to their default dashboard
      return <Navigate to={getDashboardForUser(user)} replace />;
    }
  }

  return <>{children}</>;
};

