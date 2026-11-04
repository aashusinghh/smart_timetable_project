import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth, getDashboardForUser } from './store/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { AdminDashboard } from './pages/AdminDashboard';
import { CoordinatorDashboard } from './pages/CoordinatorDashboard';
import { ProfessorDashboard } from './pages/ProfessorDashboard';
import { DepartmentsPage } from './pages/DepartmentsPage';
import { BranchesPage } from './pages/BranchesPage';
import { RoomsPage } from './pages/RoomsPage';
import { AcademicTermsPage } from './pages/AcademicTermsPage';
import { CoursesPage } from './pages/CoursesPage';
import { CurriculumPage } from './pages/CurriculumPage';
import { CohortsPage } from './pages/CohortsPage';
import { TeachingAssignmentsPage } from './pages/TeachingAssignmentsPage';
import { ProfessorsPage } from './pages/ProfessorsPage';
import { ImportPage } from './pages/ImportPage';
import { TimetablePlannerPage } from './pages/TimetablePlannerPage';
import { MyTimetablePage } from './pages/MyTimetablePage';
import { BranchTimetablePage } from './pages/BranchTimetablePage';
import { ScheduleReviewPage } from './pages/ScheduleReviewPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { HolidaysPage } from './pages/HolidaysPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 2, // 2 minutes
    },
  },
});

const RootRedirect: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (isAuthenticated && user) {
    return <Navigate to={getDashboardForUser(user)} replace />;
  }

  return <Navigate to="/login" replace />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Auth */}
            <Route path="/login" element={<LoginPage />} />

            {/* Root */}
            <Route path="/" element={<RootRedirect />} />

            {/* Protected Application Routes */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              {/* Role-Specific Dashboards */}
              <Route
                path="/dashboard/admin"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <AdminDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/dashboard/coordinator"
                element={
                  <ProtectedRoute allowedRoles={['BRANCH_COORDINATOR']}>
                    <CoordinatorDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/dashboard/professor"
                element={
                  <ProtectedRoute allowedRoles={['PROFESSOR']}>
                    <ProfessorDashboard />
                  </ProtectedRoute>
                }
              />

              {/* Master Data Management (Admin only) */}
              <Route
                path="/departments"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <DepartmentsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/branches"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <BranchesPage />
                  </ProtectedRoute>
                }
              />

              {/* Phase 2: Facilities & Academic Setup */}
              <Route
                path="/rooms"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <RoomsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/terms"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <AcademicTermsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/courses"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'BRANCH_COORDINATOR']}>
                    <CoursesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/curriculum"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'BRANCH_COORDINATOR']}>
                    <CurriculumPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/cohorts"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'BRANCH_COORDINATOR']}>
                    <CohortsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/assignments"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'BRANCH_COORDINATOR']}>
                    <TeachingAssignmentsPage />
                  </ProtectedRoute>
                }
              />

              {/* Phase 2: Faculty & CSV Ingestion */}
              <Route
                path="/professors"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <ProfessorsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/import"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <ImportPage />
                  </ProtectedRoute>
                }
              />

              {/* Phase 3 & 4: Timetable Operations */}
              <Route
                path="/timetable"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'BRANCH_COORDINATOR']}>
                    <TimetablePlannerPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/my-timetable"
                element={
                  <ProtectedRoute allowedRoles={['PROFESSOR', 'SUPER_ADMIN']}>
                    <MyTimetablePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/branches/timetable"
                element={<BranchTimetablePage />}
              />
              <Route
                path="/branches/:id/timetable"
                element={<BranchTimetablePage />}
              />
              <Route
                path="/schedule-review"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <ScheduleReviewPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/audit-logs"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                    <AuditLogsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/holidays"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'BRANCH_COORDINATOR']}>
                    <HolidaysPage />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<RootRedirect />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
