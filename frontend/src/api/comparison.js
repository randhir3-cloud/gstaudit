import { API_BASE, apiFetch, authHeaders } from './client';
import { pollJob } from './jobs';

export async function runGstr1EwayComparison(sessionId, { gstr1Base64 = '', ewbBase64 = '' } = {}) {
  const res = await fetch(`${API_BASE}/api/comparison/gstr1-eway`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      session_id: sessionId,
      gstr1_workbook_base64: gstr1Base64,
      ewb_outward_workbook_base64: ewbBase64,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Comparison failed (${res.status})`);
  }
  const body = await res.json();
  if (body.job_id) {
    return pollJob(body.job_id);
  }
  return body;
}

export async function fetchComparison(sessionId) {
  try {
    return await apiFetch(`${API_BASE}/api/comparison/${encodeURIComponent(sessionId)}`);
  } catch {
    return null;
  }
}

export async function fetchComparisonSummary(sessionId) {
  try {
    return await apiFetch(`${API_BASE}/api/comparison/${encodeURIComponent(sessionId)}/summary`);
  } catch {
    return null;
  }
}

export async function fetchComparisonDetails(sessionId, resultType, { offset = 0, limit = 100 } = {}) {
  const params = new URLSearchParams({ offset, limit });
  if (resultType) params.set('result_type', resultType);
  try {
    return await apiFetch(`${API_BASE}/api/comparison/${encodeURIComponent(sessionId)}/details?${params}`);
  } catch {
    return { records: [], total: 0 };
  }
}

export async function fetchComparisonRisk(sessionId) {
  try {
    return await apiFetch(`${API_BASE}/api/comparison/${encodeURIComponent(sessionId)}/risk`);
  } catch {
    return null;
  }
}

export async function fetchComparisonObservations(sessionId) {
  try {
    return await apiFetch(`${API_BASE}/api/comparison/${encodeURIComponent(sessionId)}/observations`);
  } catch {
    return { observations: [] };
  }
}

export async function cacheWorkbook(sessionId, datasetKey, workbookBase64) {
  return apiFetch(`${API_BASE}/api/comparison/cache-workbook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, dataset_key: datasetKey, workbook_base64: workbookBase64 }),
  });
}
