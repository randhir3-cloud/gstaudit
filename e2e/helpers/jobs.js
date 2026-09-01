/** Poll a background job until completed (for E2E seed helpers). */
import { authHeaders } from './auth.js';

export async function waitForJob(request, jobId, { timeoutMs = 60000, intervalMs = 500 } = {}) {
  const headers = authHeaders();
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const res = await request.get(`http://127.0.0.1:8000/api/jobs/${jobId}`, { headers });
    if (!res.ok()) throw new Error(`Job poll failed: ${res.status()}`);
    const job = await res.json();
    if (job.status === 'completed') return job;
    if (job.status === 'failed') throw new Error(job.error || 'Job failed');
    if (job.status === 'cancelled') throw new Error('Job cancelled');
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Job ${jobId} timed out`);
}

export async function waitForJobType(request, sessionId, jobType, { timeoutMs = 60000, intervalMs = 500 } = {}) {
  const headers = authHeaders();
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const res = await request.get(`http://127.0.0.1:8000/api/jobs?session_id=${encodeURIComponent(sessionId)}`, { headers });
    if (!res.ok()) throw new Error(`Job list failed: ${res.status()}`);
    const { jobs } = await res.json();
    const match = jobs.find((j) => j.job_type === jobType);
    if (match?.status === 'completed') return match;
    if (match?.status === 'failed') throw new Error(match.error || `${jobType} job failed`);
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`${jobType} job timed out for session ${sessionId}`);
}

export async function runComparisonJob(request, sessionId, gstr1B64, ewbB64) {
  const headers = authHeaders();
  const cmp = await request.post('http://127.0.0.1:8000/api/comparison/gstr1-eway', {
    headers,
    data: { session_id: sessionId, gstr1_workbook_base64: gstr1B64, ewb_outward_workbook_base64: ewbB64 },
  });
  if (cmp.status() !== 202) throw new Error(`Comparison enqueue failed: ${cmp.status()}`);
  const { job_id } = await cmp.json();
  const comparisonJob = await waitForJob(request, job_id);
  const intelligenceJob = await waitForJobType(request, sessionId, 'intelligence');
  return { comparisonJob, intelligenceJob };
}
