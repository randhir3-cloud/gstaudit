import { useCallback, useState } from 'react';
import * as intelligenceApi from '../api/intelligence';
import { useAuditSession } from '../context/AuditSessionContext';

export function useIntelligence() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const result = await intelligenceApi.fetchIntelligence(sessionId);
      setData(result);
      return result;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  return { sessionId, data, loading, load };
}
