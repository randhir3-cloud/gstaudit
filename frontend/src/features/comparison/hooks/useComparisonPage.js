import { useCallback, useEffect, useState } from 'react';
import { useAuditSession } from '../../../context/AuditSessionContext';
import { useDealer } from '../../../context/DealerContext';
import { comparisonService } from '../../../services/comparisonService';

/** Comparison page orchestration — page → hook → service → API */
export function useComparisonPage() {
  const { session, dashboard, refreshDashboard } = useAuditSession();
  const { hasDealer } = useDealer();
  const sessionId = session?.session_id;

  const [comparison, setComparison] = useState(null);
  const [risk, setRisk] = useState(null);
  const [observations, setObservations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadComparison = useCallback(async () => {
    if (!sessionId) return;
    const data = await comparisonService.fetchComparison(sessionId);
    setComparison(data);
    if (data?.status === 'completed') {
      setRisk(await comparisonService.fetchRisk(sessionId));
      const obs = await comparisonService.fetchObservations(sessionId);
      setObservations(obs.observations || []);
    } else {
      setRisk(null);
      setObservations([]);
    }
  }, [sessionId]);

  useEffect(() => {
    loadComparison();
  }, [loadComparison, dashboard?.session?.updated_at]);

  const runComparison = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError('');
    try {
      await comparisonService.runGstr1Eway(sessionId);
      await refreshDashboard();
      await loadComparison();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshDashboard, loadComparison]);

  const pair = dashboard?.comparison_status?.find((p) => p.id === 'gstr1_ewb_outward');
  const canRun = pair?.status === 'ready' || pair?.status === 'completed';

  return {
    sessionId,
    hasDealer,
    comparison,
    risk,
    observations,
    loading,
    error,
    pair,
    canRun,
    runComparison,
  };
}

export default useComparisonPage;
