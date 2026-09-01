import { useAuditSession } from '../context/AuditSessionContext';

export function useDashboard() {
  const {
    session,
    dashboard,
    refreshDashboard,
    loading,
    resolveDuplicate,
    hasSession,
    recordUpload,
    recordMerge,
  } = useAuditSession();

  return {
    sessionId: session?.session_id,
    session,
    dashboard,
    refreshDashboard,
    loading,
    resolveDuplicate,
    hasSession,
    recordUpload,
    recordMerge,
  };
}

export { useDashboardStats, useReadiness } from './useDashboardStats';
