import { useCallback, useState } from 'react';
import * as comparisonApi from '../api/comparison';
import { useAuditSession } from '../context/AuditSessionContext';

export function useComparison() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  const runComparison = useCallback(async (options) => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      await comparisonApi.runGstr1EwayComparison(sessionId, options);
      const s = await comparisonApi.fetchComparisonSummary(sessionId);
      setSummary(s);
      return s;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const loadSummary = useCallback(async () => {
    if (!sessionId) return;
    const s = await comparisonApi.fetchComparisonSummary(sessionId);
    setSummary(s);
    return s;
  }, [sessionId]);

  return { sessionId, loading, error, summary, runComparison, loadSummary };
}
