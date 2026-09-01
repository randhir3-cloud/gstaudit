import { API_BASE, apiFetch, buildQuery } from './client';

export async function syncSession(session) {
  return apiFetch(`${API_BASE}/api/session/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(session),
  });
}

export async function fetchDashboard(sessionId) {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return apiFetch(`${API_BASE}/api/dashboard${params}`);
}

export async function fetchMonthCoverage(sessionId) {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return apiFetch(`${API_BASE}/api/dashboard/month-coverage${params}`);
}

export async function fetchStatistics(sessionId) {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return apiFetch(`${API_BASE}/api/dashboard/statistics${params}`);
}

export async function fetchUploadHistory(sessionId) {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return apiFetch(`${API_BASE}/api/dashboard/upload-history${params}`);
}

export async function fetchDiscrepancies(sessionId) {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return apiFetch(`${API_BASE}/api/dashboard/discrepancies${params}`);
}

export async function fetchReadiness(sessionId) {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return apiFetch(`${API_BASE}/api/dashboard/readiness${params}`);
}

export { buildQuery };
