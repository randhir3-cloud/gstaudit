import { useCallback, useEffect, useState } from 'react';
import { useAuditSession } from '../../../context/AuditSessionContext';
import { investigationService } from '../../../services/investigationService';

export function useInvestigationPage() {
  const { session, dashboard, refreshDashboard } = useAuditSession();
  const sessionId = session?.session_id || dashboard?.session?.session_id || '';

  const [data, setData] = useState(null);
  const [category, setCategory] = useState('ALL');
  const [selectedCase, setSelectedCase] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [filters, setFilters] = useState({ search: '', status: '', gstin: '', month: '' });

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const params = { category: category === 'ALL' ? undefined : category, limit: 200 };
      if (filters.search) params.search = filters.search;
      if (filters.status) params.status = filters.status;
      if (filters.gstin) params.gstin = filters.gstin;
      if (filters.month) params.month = filters.month;
      if (category === 'HIGH_RISK') params.high_risk_only = 'true';
      const result = await investigationService.fetchCases(sessionId, params);
      setData(result);
    } finally {
      setLoading(false);
    }
  }, [sessionId, category, filters]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (sessionId) refreshDashboard();
  }, [sessionId, refreshDashboard]);

  const saveCase = useCallback(async (payload) => {
    if (!selectedCase) return;
    setSaving(true);
    try {
      await investigationService.updateCase(selectedCase.case_id, { session_id: sessionId, ...payload });
      await load();
      const refreshed = await investigationService.fetchCases(sessionId, { limit: 200 });
      const updated = refreshed.cases.find((c) => c.case_id === selectedCase.case_id);
      if (updated) setSelectedCase(updated);
    } finally {
      setSaving(false);
    }
  }, [selectedCase, sessionId, load]);

  const bulkUpdate = useCallback(async (status) => {
    if (!selectedIds.length) return;
    await investigationService.bulkUpdate({
      session_id: sessionId,
      case_ids: selectedIds,
      status,
      officer_remarks: 'Bulk update',
    });
    setSelectedIds([]);
    await load();
  }, [selectedIds, sessionId, load]);

  const toggleSelect = useCallback((id) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }, []);

  const selectAll = useCallback((checked, rows) => {
    setSelectedIds(checked ? rows.map((r) => r.case_id) : []);
  }, []);

  return {
    sessionId,
    data,
    category,
    setCategory,
    selectedCase,
    setSelectedCase,
    selectedIds,
    loading,
    saving,
    filters,
    setFilters,
    saveCase,
    bulkUpdate,
    toggleSelect,
    selectAll,
  };
}

export default useInvestigationPage;
