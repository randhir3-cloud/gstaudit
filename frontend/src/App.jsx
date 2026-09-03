import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DealerProvider } from './context/DealerContext';
import { EwayProvider } from './context/EwayContext';
import { AuditSessionProvider } from './context/AuditSessionContext';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/auth/ProtectedRoute';

// Pages — all imports retained; source code is NOT deleted.
import Dashboard from './pages/Dashboard';
import MergePage from './pages/MergePage';
import WorkbookViewer from './pages/WorkbookViewer';
import ComparisonScreen from './pages/ComparisonScreen';
import InvestigationPage from './pages/InvestigationPage';
import AuditReportPreview from './pages/AuditReportPreview';
import LoginPage from './pages/LoginPage';
import AdminPage from './pages/AdminPage';
import SystemMonitorPage from './pages/SystemMonitorPage';
import AuditIntelligenceCenter from './pages/AuditIntelligenceCenter';
import AuditCaseManagementPage from './pages/AuditCaseManagementPage';
import OfficerTasksPage from './pages/OfficerTasksPage';
import SupervisorDashboardPage from './pages/SupervisorDashboardPage';

// Feature configuration — single source of truth for module availability.
import { isModuleEnabled, DEFAULT_ROUTE } from './config/appModules';

/**
 * ModuleRoute: wraps a route element with a feature-availability check.
 * If the module is disabled → redirect to DEFAULT_ROUTE (/merge).
 * Authentication and permission checks remain intact inside ProtectedRoute.
 *
 * Logic order:  authenticated? → authorized? → module enabled?
 */
function ModuleRoute({ moduleKey, children }) {
  if (!isModuleEnabled(moduleKey)) {
    return <Navigate to={DEFAULT_ROUTE} replace />;
  }
  return children;
}

function App() {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') || 'dark';
    }
    return 'dark';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') root.classList.add('dark');
    else root.classList.remove('dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <AuthProvider>
    <DealerProvider>
      <AuditSessionProvider>
      <EwayProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout
                  theme={theme}
                  onToggleTheme={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
                />
              </ProtectedRoute>
            }
          >
            {/* Default landing: redirect root → /merge (the current active module). */}
            <Route index element={<Navigate to={DEFAULT_ROUTE} replace />} />

            {/* ── ENABLED MODULE ─────────────────────────────────────────── */}
            <Route
              path="merge"
              element={
                <ProtectedRoute permission="merge_files">
                  <MergePage />
                </ProtectedRoute>
              }
            />

            {/* ── DISABLED MODULES ───────────────────────────────────────── */}
            {/* Source code & imports above are preserved. Routes redirect to  */}
            {/* /merge until the module is re-enabled in appModules.js.        */}
            <Route
              path="/"
              element={
                <ModuleRoute moduleKey="dashboard">
                  <Dashboard />
                </ModuleRoute>
              }
            />
            <Route
              path="workbook"
              element={
                <ModuleRoute moduleKey="workbookViewer">
                  <WorkbookViewer />
                </ModuleRoute>
              }
            />
            <Route
              path="comparison"
              element={
                <ModuleRoute moduleKey="comparison">
                  <ComparisonScreen />
                </ModuleRoute>
              }
            />
            <Route
              path="investigation"
              element={
                <ModuleRoute moduleKey="investigation">
                  <ProtectedRoute permission="update_cases">
                    <InvestigationPage />
                  </ProtectedRoute>
                </ModuleRoute>
              }
            />
            <Route
              path="audit-intelligence"
              element={
                <ModuleRoute moduleKey="auditIntelligence">
                  <ProtectedRoute permission="view_intelligence">
                    <AuditIntelligenceCenter />
                  </ProtectedRoute>
                </ModuleRoute>
              }
            />
            <Route
              path="audit-cases"
              element={
                <ModuleRoute moduleKey="caseManagement">
                  <ProtectedRoute permission="manage_audit_cases">
                    <AuditCaseManagementPage />
                  </ProtectedRoute>
                </ModuleRoute>
              }
            />
            <Route
              path="officer-tasks"
              element={
                <ModuleRoute moduleKey="officerTasks">
                  <ProtectedRoute permission="manage_audit_cases">
                    <OfficerTasksPage />
                  </ProtectedRoute>
                </ModuleRoute>
              }
            />
            <Route
              path="supervisor-dashboard"
              element={
                <ModuleRoute moduleKey="supervisor">
                  <ProtectedRoute permission="supervise_audit_cases">
                    <SupervisorDashboardPage />
                  </ProtectedRoute>
                </ModuleRoute>
              }
            />
            <Route
              path="audit-report"
              element={
                <ModuleRoute moduleKey="auditReport">
                  <ProtectedRoute permission="view_reports">
                    <AuditReportPreview />
                  </ProtectedRoute>
                </ModuleRoute>
              }
            />
            <Route
              path="admin"
              element={
                <ModuleRoute moduleKey="administration">
                  <AdminPage />
                </ModuleRoute>
              }
            />
            <Route
              path="system-monitor"
              element={
                <ModuleRoute moduleKey="systemMonitor">
                  <SystemMonitorPage />
                </ModuleRoute>
              }
            />

            {/* Unknown routes: no catch-all here so BrowserRouter's default
                404 behaviour is preserved. Unknown URLs will not silently
                redirect to /merge — only known disabled module routes do. */}
          </Route>
        </Routes>
      </BrowserRouter>
      </EwayProvider>
      </AuditSessionProvider>
    </DealerProvider>
    </AuthProvider>
  );
}

export default App;
