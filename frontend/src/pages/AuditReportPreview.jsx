import React, { useEffect, useState } from 'react';
import { Download, FileSpreadsheet, FileText, Loader2, FileType } from 'lucide-react';
import DealerHeader from '../components/DealerHeader';
import { useAuditSession } from '../context/AuditSessionContext';
import { fetchReportPreview, generateReport } from '../api/investigation';

export default function AuditReportPreview() {
  const { session, dashboard } = useAuditSession();
  const sessionId = session?.session_id || dashboard?.session?.session_id || '';
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!sessionId) return;
    fetchReportPreview(sessionId).then(setPreview).catch(() => {});
  }, [sessionId, dashboard?.case_tracking]);

  const handleGenerate = async (format) => {
    if (!sessionId) {
      setError('Load audit session before generating report.');
      return;
    }
    setError('');
    setLoading(format);
    try {
      await generateReport(sessionId, format);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading('');
    }
  };

  const es = preview?.executive_summary;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-zinc-950 dark:text-white">Audit Report</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">Generate official GAIS audit report with executive summary and observations.</p>
      </div>

      <DealerHeader />

      {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700" data-testid="report-error">{error}</div>}

      <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6" data-testid="report-export-panel">
        <h3 className="font-semibold mb-4">Generate Report</h3>
        <div className="flex flex-wrap gap-3">
          <ExportBtn format="excel" icon={FileSpreadsheet} label="Excel" loading={loading} onClick={handleGenerate} testId="export-excel" />
          <ExportBtn format="pdf" icon={FileText} label="PDF" loading={loading} onClick={handleGenerate} testId="export-pdf" />
          <ExportBtn format="docx" icon={FileType} label="Word" loading={loading} onClick={handleGenerate} testId="export-docx" />
        </div>
      </div>

      {es && (
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 space-y-4" data-testid="report-preview">
          <h3 className="font-semibold flex items-center gap-2"><Download className="h-4 w-4" /> Executive Summary Preview</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
            <PreviewItem label="Dealer" value={es.dealer} testId="preview-dealer" />
            <PreviewItem label="GSTIN" value={es.gstin} testId="preview-gstin" />
            <PreviewItem label="Financial Year" value={es.financial_year} testId="preview-fy" />
            <PreviewItem label="Matched" value={es.matched} testId="preview-matched" />
            <PreviewItem label="Missing" value={es.missing} testId="preview-missing" />
            <PreviewItem label="Risk Level" value={es.risk_level} testId="preview-risk" />
          </div>
          <p className="text-sm rounded-lg bg-zinc-50 dark:bg-zinc-950 p-3" data-testid="preview-conclusion"><strong>Conclusion:</strong> {es.audit_conclusion}</p>
          {preview.recommendations?.length > 0 && (
            <div>
              <h4 className="font-semibold text-sm mb-2">Recommendations</h4>
              <ul className="text-sm list-disc list-inside space-y-1">{preview.recommendations.map((r) => <li key={r}>{r}</li>)}</ul>
            </div>
          )}
        </div>
      )}

      {preview?.audit_intelligence?.patterns?.length > 0 && (
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 space-y-4" data-testid="report-intelligence-section">
          <h3 className="font-semibold">Audit Intelligence</h3>
          <div>
            <h4 className="text-sm font-semibold mb-2">Pattern Analysis</h4>
            <ul className="text-sm space-y-1">{preview.audit_intelligence.patterns.slice(0, 5).map((p) => (
              <li key={p.pattern_type + p.description} className="rounded-lg bg-zinc-50 dark:bg-zinc-950 px-3 py-2">{p.description}</li>
            ))}</ul>
          </div>
          {preview.audit_intelligence.high_risk_months?.length > 0 && (
            <div data-testid="report-high-risk-months">
              <h4 className="text-sm font-semibold mb-2">High Risk Months</h4>
              <p className="text-sm">{preview.audit_intelligence.high_risk_months.join(', ')}</p>
            </div>
          )}
          {preview.audit_intelligence.top_suppliers?.length > 0 && (
            <div data-testid="report-top-suppliers">
              <h4 className="text-sm font-semibold mb-2">Top Supplier Risks</h4>
              <ul className="text-sm list-disc list-inside">{preview.audit_intelligence.top_suppliers.slice(0, 5).map((s) => (
                <li key={s.gstin}>{s.gstin} — {s.mismatch_count} mismatches (₹{s.value_difference?.toLocaleString?.('en-IN')})</li>
              ))}</ul>
            </div>
          )}
          {preview.audit_intelligence.suggested_documents?.length > 0 && (
            <div data-testid="report-suggested-documents">
              <h4 className="text-sm font-semibold mb-2">Suggested Documents</h4>
              <ul className="text-sm list-disc list-inside">{preview.audit_intelligence.suggested_documents.slice(0, 4).map((d) => (
                <li key={d.discrepancy_type}>{d.discrepancy_type}: {d.documents?.slice(0, 3).join(', ')}</li>
              ))}</ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ExportBtn({ format, icon: Icon, label, loading, onClick, testId }) {
  return (
    <button type="button" disabled={!!loading} onClick={() => onClick(format)} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium" data-testid={testId}>
      {loading === format ? <Loader2 className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
      {label}
    </button>
  );
}

function PreviewItem({ label, value, testId }) {
  return (
    <div className="rounded-lg bg-zinc-50 dark:bg-zinc-950 p-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="font-semibold" data-testid={testId}>{value ?? '—'}</p>
    </div>
  );
}
