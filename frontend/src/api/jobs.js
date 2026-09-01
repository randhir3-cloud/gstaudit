import { API_BASE, apiFetch, authHeaders } from './client';

export async function createJob(body) {
  return apiFetch(`${API_BASE}/api/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function fetchJobs(sessionId) {
  const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
  return apiFetch(`${API_BASE}/api/jobs${params}`);
}

export async function fetchJob(jobId) {
  return apiFetch(`${API_BASE}/api/jobs/${encodeURIComponent(jobId)}`);
}

export async function cancelJob(jobId) {
  return apiFetch(`${API_BASE}/api/jobs/${encodeURIComponent(jobId)}/cancel`, { method: 'POST' });
}

export async function retryJob(jobId) {
  return apiFetch(`${API_BASE}/api/jobs/${encodeURIComponent(jobId)}/retry`, { method: 'POST' });
}

export async function downloadJobResult(jobId) {
  const res = await fetch(`${API_BASE}/api/jobs/${encodeURIComponent(jobId)}/download`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  const blob = await res.blob();
  const disposition = res.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="(.+)"/);
  return { blob, filename: match?.[1] || 'report.xlsx' };
}

export async function pollJob(jobId, { intervalMs = 500, timeoutMs = 120000 } = {}) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const job = await fetchJob(jobId);
    if (job.status === 'completed') return job;
    if (job.status === 'failed') throw new Error(job.error || 'Job failed');
    if (job.status === 'cancelled') throw new Error('Job cancelled');
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error('Job timed out');
}

export function jobsWebSocketUrl(sessionId) {
  const base = API_BASE.replace(/^http/, 'ws');
  return `${base}/ws/jobs/${encodeURIComponent(sessionId)}`;
}
