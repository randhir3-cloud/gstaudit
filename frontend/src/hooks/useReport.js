import { useCallback, useState } from 'react';
import { fetchReportPreview, generateReport } from '../api/investigation';
import { useAuditSession } from '../context/AuditSessionContext';

export function useReport() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadPreview = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await fetchReportPreview(sessionId);
      setPreview(data);
      return data;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const exportReport = useCallback(async (format, options = {}) => {
    if (!sessionId) return;
    await generateReport(sessionId, format, options);
  }, [sessionId]);

  return { sessionId, preview, loading, loadPreview, exportReport };
}
