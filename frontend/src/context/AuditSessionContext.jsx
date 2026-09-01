import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { EMPTY_DEALER } from '../types/dealer';
import {
  DATASET_LABELS,
  STORAGE_KEY,
  buildEmptyDatasets,
  buildSessionId,
} from '../types/auditSession';
import { syncSession, fetchDashboard } from '../api/dashboard';

const AuditSessionContext = createContext(null);

function loadStoredSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function createEmptySession() {
  return {
    session_id: '',
    dealer: { ...EMPTY_DEALER },
    financial_year: '',
    tax_period: '',
    audit_status: 'draft',
    datasets: buildEmptyDatasets(),
    upload_history: [],
    comparison_status: [],
    discrepancies: {
      missing_invoice: 0,
      duplicate_invoice: 0,
      gstin_mismatch: 0,
      invoice_mismatch: 0,
      value_mismatch: 0,
      date_mismatch: 0,
      hsn_mismatch: 0,
      state_mismatch: 0,
      risk_score: 0,
      total: 0,
    },
    created_at: '',
    updated_at: '',
  };
}

export function AuditSessionProvider({ children }) {
  const [session, setSession] = useState(() => loadStoredSession() || createEmptySession());
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const syncTimer = useRef(null);

  const persistAndSync = useCallback((nextSession) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
    if (syncTimer.current) clearTimeout(syncTimer.current);
    syncTimer.current = setTimeout(async () => {
      try {
        const dash = await syncSession(nextSession);
        setDashboard(dash);
      } catch {
        /* offline — local state still valid */
      }
    }, 400);
  }, []);

  const refreshDashboard = useCallback(async () => {
    if (!session.session_id) return;
    setLoading(true);
    try {
      const dash = await fetchDashboard(session.session_id);
      setDashboard(dash);
    } finally {
      setLoading(false);
    }
  }, [session.session_id]);

  useEffect(() => {
    if (session.session_id) {
      refreshDashboard();
    }
  }, [session.session_id, refreshDashboard]);

  const ensureSessionIdentity = useCallback((dealer) => {
    const gstin = dealer?.gstin || '';
    const fy = dealer?.financial_year || '';
    if (!gstin) return session;
    const sessionId = buildSessionId(gstin, fy);
    return {
      ...session,
      session_id: sessionId,
      dealer: { ...session.dealer, ...dealer },
      financial_year: fy || session.financial_year,
      tax_period: dealer?.tax_period || session.tax_period,
    };
  }, [session]);

  const recordUpload = useCallback((datasetKey, filenames, dealer, rows = 0) => {
    setSession((prev) => {
      const base = ensureSessionIdentity(dealer || prev.dealer);
      const now = new Date().toISOString();
      const ds = { ...base.datasets[datasetKey] };
      const combined = [...new Set([...ds.staged_files, ...filenames])];
      ds.staged_files = combined;
      ds.dealer_gstin = dealer?.gstin || ds.dealer_gstin;
      ds.financial_year = dealer?.financial_year || ds.financial_year;
      ds.last_upload_at = now;
      ds.status = ds.merged ? 'merged' : 'uploaded';
      if (rows) ds.row_count = rows;

      const history = [
        ...base.upload_history,
        ...filenames.map((name) => ({
          timestamp: now,
          dataset: datasetKey,
          dataset_label: DATASET_LABELS[datasetKey],
          month: '',
          filename: name,
          rows,
          status: 'uploaded',
        })),
      ];

      const next = {
        ...base,
        datasets: { ...base.datasets, [datasetKey]: ds },
        upload_history: history,
        updated_at: now,
        created_at: base.created_at || now,
      };
      persistAndSync(next);
      return next;
    });
  }, [ensureSessionIdentity, persistAndSync]);

  const recordMerge = useCallback((datasetKey, payload) => {
    setSession((prev) => {
      const dealer = payload.dealer || prev.dealer;
      const base = ensureSessionIdentity(dealer);
      const now = new Date().toISOString();
      const sourceFiles = payload.source_files || payload.summary?.source_files || [];
      const ds = {
        ...base.datasets[datasetKey],
        source_files: sourceFiles,
        staged_files: [],
        merged: true,
        workbook_id: payload.workbook_id || '',
        current_dataset: payload.suggested_filename || payload.current_dataset || '',
        dealer_gstin: dealer?.gstin || '',
        financial_year: payload.financial_year || dealer?.financial_year || '',
        row_count: payload.row_count || payload.summary?.row_count || 0,
        invoice_count: datasetKey.startsWith('ewb_') ? 0 : (payload.row_count || 0),
        uploaded_months: payload.uploaded_months || payload.summary?.uploaded_months || [],
        missing_months: payload.missing_months || payload.summary?.missing_months || [],
        last_merge_at: now,
        merge_processing_ms: payload.processing_ms || 0,
        status: 'merged',
        preview_available: true,
        download_available: true,
      };

      const next = {
        ...base,
        dealer: { ...base.dealer, ...dealer },
        financial_year: ds.financial_year || base.financial_year,
        datasets: { ...base.datasets, [datasetKey]: ds },
        updated_at: now,
        created_at: base.created_at || now,
      };
      persistAndSync(next);
      return next;
    });
  }, [ensureSessionIdentity, persistAndSync]);

  const resolveDuplicate = useCallback((datasetKey, month, action, keepFilename) => {
    setSession((prev) => {
      const ds = { ...prev.datasets[datasetKey] };
      const allFiles = [...ds.source_files, ...ds.staged_files];
      const monthShort = month.split(' ')[0]?.slice(0, 3).toLowerCase();
      const monthMap = { jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06', jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12' };
      const mm = monthMap[monthShort] || '';

      const grouped = allFiles.filter((f) => f.includes(`_${mm}`));
      let kept = allFiles;
      if (action === 'keep_latest' && grouped.length > 1) {
        const latest = grouped[grouped.length - 1];
        kept = allFiles.filter((f) => !grouped.includes(f) || f === latest);
      } else if (action === 'replace' && keepFilename) {
        kept = allFiles.filter((f) => !grouped.includes(f) || f === keepFilename);
      } else if (action === 'delete' && keepFilename) {
        kept = allFiles.filter((f) => f !== keepFilename);
      }

      ds.staged_files = kept.filter((f) => !ds.source_files.includes(f));
      if (!ds.merged) ds.source_files = [];
      else ds.source_files = kept;

      ds.duplicate_months = ds.duplicate_months.map((d) =>
        d.month === month ? { ...d, resolution: action } : d,
      );

      const next = { ...prev, datasets: { ...prev.datasets, [datasetKey]: ds }, updated_at: new Date().toISOString() };
      persistAndSync(next);
      return next;
    });
  }, [persistAndSync]);

  const clearSession = useCallback(() => {
    const empty = createEmptySession();
    localStorage.removeItem(STORAGE_KEY);
    setSession(empty);
    setDashboard(null);
  }, []);

  const value = useMemo(
    () => ({
      session,
      dashboard,
      loading,
      recordUpload,
      recordMerge,
      resolveDuplicate,
      refreshDashboard,
      clearSession,
      hasSession: Boolean(session.dealer?.gstin),
    }),
    [session, dashboard, loading, recordUpload, recordMerge, resolveDuplicate, refreshDashboard, clearSession],
  );

  return <AuditSessionContext.Provider value={value}>{children}</AuditSessionContext.Provider>;
}

export function useAuditSession() {
  const ctx = useContext(AuditSessionContext);
  if (!ctx) throw new Error('useAuditSession must be used within AuditSessionProvider');
  return ctx;
}
