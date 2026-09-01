import { API_BASE, apiFetch } from './client';

export async function fetchAuditCases(sessionId, params = {}) {
  const qs = new URLSearchParams({ session_id: sessionId, ...params });
  return apiFetch(`${API_BASE}/api/audit-cases?${qs}`);
}

export async function fetchAuditCaseDetail(sessionId, auditCaseId) {
  return apiFetch(
    `${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}?session_id=${encodeURIComponent(sessionId)}`,
  );
}

export async function fetchCaseTransitions(sessionId, auditCaseId) {
  return apiFetch(
    `${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/transitions?session_id=${encodeURIComponent(sessionId)}`,
  );
}

export async function assignAuditCase(auditCaseId, body) {
  return apiFetch(`${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/assign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function transitionAuditCase(auditCaseId, body) {
  return apiFetch(`${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/transition`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function approveAuditCase(auditCaseId, sessionId, supervisor = 'supervisor', remarks = '') {
  const qs = new URLSearchParams({ session_id: sessionId, supervisor, remarks });
  return apiFetch(`${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/approve?${qs}`, {
    method: 'POST',
  });
}

export async function createCaseNotice(auditCaseId, body) {
  return apiFetch(`${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/notices`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function issueCaseNotice(auditCaseId, noticeId, sessionId, actor = 'officer') {
  const qs = new URLSearchParams({ session_id: sessionId, actor });
  return apiFetch(
    `${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/notices/${encodeURIComponent(noticeId)}/issue?${qs}`,
    { method: 'POST' },
  );
}

export async function addCaseComment(auditCaseId, body) {
  return apiFetch(`${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function recordDealerResponse(auditCaseId, body) {
  return apiFetch(`${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/dealer-response`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function uploadCaseDocument(auditCaseId, formData) {
  return apiFetch(`${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/documents`, {
    method: 'POST',
    body: formData,
  });
}

export async function fetchOfficerTasks(sessionId, officer = '') {
  const qs = new URLSearchParams({ session_id: sessionId, officer });
  return apiFetch(`${API_BASE}/api/audit-cases/tasks?${qs}`);
}

export async function fetchSupervisorDashboard(sessionId) {
  return apiFetch(`${API_BASE}/api/audit-cases/supervisor?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchCaseReport(sessionId, auditCaseId) {
  return apiFetch(
    `${API_BASE}/api/audit-cases/${encodeURIComponent(auditCaseId)}/report?session_id=${encodeURIComponent(sessionId)}`,
  );
}
