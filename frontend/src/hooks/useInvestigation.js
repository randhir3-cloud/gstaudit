import { useCallback, useState } from 'react';
import { fetchInvestigation } from '../api/investigation';
import { useAuditSession } from '../context/AuditSessionContext';

export function useInvestigation() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadCases = useCallback(async (params = {}) => {
    if (!sessionId) return [];
    setLoading(true);
    try {
      const data = await fetchInvestigation(sessionId, params);
      setCases(data.cases || data);
      return data;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  return { sessionId, cases, loading, loadCases };
}
