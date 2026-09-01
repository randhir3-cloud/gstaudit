/** Unified API client — single base URL, auth, and error handling. */
export const API_BASE = import.meta.env.VITE_API_BASE ?? '';

const TOKEN_KEY = 'gais_access_token';

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function authHeaders(extra = {}) {
  const token = getAccessToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

export function setAccessToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch(path, options = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
  const headers = { ...(options.headers || {}) };
  const token = getAccessToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers, credentials: options.credentials ?? 'include' });

  if (response.status === 401 && !path.includes('/api/auth/login')) {
    setAccessToken(null);
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || body.message || detail;
    } catch {
      // non-JSON error body
    }
    const error = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    error.status = response.status;
    throw error;
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response;
}

export function buildQuery(sessionId, params = {}) {
  const qs = new URLSearchParams();
  if (sessionId) qs.set('session_id', sessionId);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      qs.set(key, String(value));
    }
  });
  return qs;
}
