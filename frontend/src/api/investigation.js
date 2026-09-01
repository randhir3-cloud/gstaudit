import { API_BASE, apiFetch, authHeaders, buildQuery } from './client';
import { downloadJobResult, pollJob } from './jobs';

export async function fetchInvestigation(sessionId, params = {}) {
  const qs = buildQuery(sessionId, params);
  return apiFetch(`${API_BASE}/api/investigation?${qs}`);
}

export async function fetchCase(sessionId, caseId) {
  return apiFetch(`${API_BASE}/api/investigation/${encodeURIComponent(caseId)}?session_id=${encodeURIComponent(sessionId)}`);
}

export async function updateCase(caseId, body) {
  return apiFetch(`${API_BASE}/api/investigation/${encodeURIComponent(caseId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function bulkUpdateCases(body) {
  return apiFetch(`${API_BASE}/api/investigation/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function fetchReportPreview(sessionId) {
  return apiFetch(`${API_BASE}/api/report/preview?session_id=${encodeURIComponent(sessionId)}`);
}

export async function generateReport(sessionId, format, options = {}) {
  const params = buildQuery(sessionId, {
    format,
    high_risk_only: options.high_risk_only ? 'true' : undefined,
    case_ids: options.case_ids?.length ? options.case_ids.join(',') : undefined,
  });
  const res = await fetch(`${API_BASE}/api/report/generate?${params}`, { method: 'POST', headers: authHeaders() });
  if (!res.ok) throw new Error('Report generation failed');
  const body = await res.json();
  if (!body.job_id) throw new Error('Expected job response');
  const job = await pollJob(body.job_id, { timeoutMs: 180000 });
  const { blob, filename } = await downloadJobResult(job.job_id);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
  return job;
}
