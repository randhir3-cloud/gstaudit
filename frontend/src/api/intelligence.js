import { API_BASE, apiFetch, buildQuery } from './client';

export async function fetchIntelligence(sessionId) {
  return apiFetch(`${API_BASE}/api/intelligence?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchIntelligenceSummary(sessionId) {
  return apiFetch(`${API_BASE}/api/intelligence/summary?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchIntelligenceMonths(sessionId) {
  return apiFetch(`${API_BASE}/api/intelligence/months?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchIntelligenceSuppliers(sessionId) {
  return apiFetch(`${API_BASE}/api/intelligence/suppliers?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchIntelligenceCustomers(sessionId) {
  return apiFetch(`${API_BASE}/api/intelligence/customers?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchIntelligenceCases(sessionId, limit = 50) {
  return apiFetch(`${API_BASE}/api/intelligence/cases?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`);
}

export { buildQuery };
