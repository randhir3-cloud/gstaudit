import { API_BASE, apiFetch } from './client';

export async function fetchMsae(sessionId) {
  return apiFetch(`${API_BASE}/api/msae?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchMsaeSummary(sessionId) {
  return apiFetch(`${API_BASE}/api/msae/summary?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchMsaeCases(sessionId, params = {}) {
  const qs = new URLSearchParams({ session_id: sessionId, ...params });
  return apiFetch(`${API_BASE}/api/msae/cases?${qs}`);
}

export async function fetchMsaeCaseDetail(sessionId, masterCaseId) {
  return apiFetch(
    `${API_BASE}/api/msae/cases/${encodeURIComponent(masterCaseId)}?session_id=${encodeURIComponent(sessionId)}`,
  );
}

export async function fetchMsaePatterns(sessionId) {
  return apiFetch(`${API_BASE}/api/msae/patterns?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchMsaeScores(sessionId) {
  return apiFetch(`${API_BASE}/api/msae/scores?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchMsaeTimeline(sessionId) {
  return apiFetch(`${API_BASE}/api/msae/timeline?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchMsaeReport(sessionId) {
  return apiFetch(`${API_BASE}/api/msae/report?session_id=${encodeURIComponent(sessionId)}`);
}

export async function orchestrateMsae(sessionId) {
  return apiFetch(`${API_BASE}/api/msae/orchestrate?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  });
}
