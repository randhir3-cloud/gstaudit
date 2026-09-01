import { useCallback, useEffect, useState } from 'react';
import { fetchStatistics, fetchReadiness } from '../api/dashboard';
import { useAuditSession } from '../context/AuditSessionContext';

export function useDashboardStats() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await fetchStatistics(sessionId);
      setStats(data);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { load(); }, [load]);

  return { stats, loading, reload: load };
}

export function useReadiness() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [readiness, setReadiness] = useState(null);

  useEffect(() => {
    if (!sessionId) return;
    fetchReadiness(sessionId).then(setReadiness).catch(() => setReadiness(null));
  }, [sessionId]);

  return readiness;
}
