import { API_BASE, apiFetch } from './client';

export async function fetchSystemHealth() {
  return apiFetch(`${API_BASE}/api/system/health`);
}

export async function fetchSystemMetrics() {
  return apiFetch(`${API_BASE}/api/system/metrics`);
}

export async function fetchSystemJobs(limit = 50) {
  return apiFetch(`${API_BASE}/api/system/jobs?limit=${limit}`);
}

export async function fetchSystemUsers() {
  return apiFetch(`${API_BASE}/api/system/users`);
}

export async function fetchSystemStorage() {
  return apiFetch(`${API_BASE}/api/system/storage`);
}

export async function fetchSystemVersion() {
  return apiFetch(`${API_BASE}/api/system/version`);
}

export async function fetchSystemConfig() {
  return apiFetch(`${API_BASE}/api/system/config`);
}

export async function fetchSystemLogs({ source, action, user, limit = 100 } = {}) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (source) params.set('source', source);
  if (action) params.set('action', action);
  if (user) params.set('user', user);
  return apiFetch(`${API_BASE}/api/system/logs?${params}`);
}

export async function exportSystemLogs(filters = {}) {
  const params = new URLSearchParams({ limit: '500' });
  if (filters.source) params.set('source', filters.source);
  if (filters.action) params.set('action', filters.action);
  if (filters.user) params.set('user', filters.user);
  return apiFetch(`${API_BASE}/api/system/logs/export?${params}`);
}
