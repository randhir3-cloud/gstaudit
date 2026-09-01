import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DealerProvider } from './context/DealerContext';
import { EwayProvider } from './context/EwayContext';
import { AuditSessionProvider } from './context/AuditSessionContext';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/auth/ProtectedRoute';
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
            <Route index element={<Dashboard />} />
            <Route path="merge" element={<ProtectedRoute permission="merge_files"><MergePage /></ProtectedRoute>} />
            <Route path="workbook" element={<WorkbookViewer />} />
            <Route path="comparison" element={<ComparisonScreen />} />
            <Route path="investigation" element={<ProtectedRoute permission="update_cases"><InvestigationPage /></ProtectedRoute>} />
            <Route path="audit-intelligence" element={<ProtectedRoute permission="view_intelligence"><AuditIntelligenceCenter /></ProtectedRoute>} />
            <Route path="audit-cases" element={<ProtectedRoute permission="manage_audit_cases"><AuditCaseManagementPage /></ProtectedRoute>} />
            <Route path="officer-tasks" element={<ProtectedRoute permission="manage_audit_cases"><OfficerTasksPage /></ProtectedRoute>} />
            <Route path="supervisor-dashboard" element={<ProtectedRoute permission="supervise_audit_cases"><SupervisorDashboardPage /></ProtectedRoute>} />
            <Route path="audit-report" element={<ProtectedRoute permission="view_reports"><AuditReportPreview /></ProtectedRoute>} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="system-monitor" element={<SystemMonitorPage />} />
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
