/** Authentication API client. */
import { API_BASE, apiFetch, setAccessToken, getAccessToken } from './client';

export function getStoredToken() {
  return getAccessToken();
}

export function setStoredToken(token) {
  setAccessToken(token);
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Login failed');
  }
  const data = await res.json();
  setStoredToken(data.access_token);
  return data;
}

export async function logout() {
  try {
    await apiFetch(`${API_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include' });
  } finally {
    setStoredToken(null);
  }
}

export async function fetchCurrentUser() {
  return apiFetch(`${API_BASE}/api/auth/me`);
}

export async function fetchSessions() {
  return apiFetch(`${API_BASE}/api/auth/sessions`);
}

export async function fetchRecentAuditLogs(limit = 10) {
  return apiFetch(`${API_BASE}/api/admin/audit-logs?limit=${limit}`);
}

export async function refreshToken() {
  const res = await fetch(`${API_BASE}/api/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('Session expired');
  const data = await res.json();
  setStoredToken(data.access_token);
  return data;
}
