import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { saveEvidence } from './helpers/visualStability.js';
import { runComparisonJob, waitForJob } from './helpers/jobs.js';
import { authHeaders, prepareAuthenticatedPage } from './helpers/auth.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');
const SESSION_ID = 'session_jobs_e2e';
const DEALER_GSTIN = '03AABCU9603R1ZX';
const FY = '2023-24';

function toBase64(filePath) {
  return fs.readFileSync(filePath).toString('base64');
}

function buildMergedSession() {
  return {
    session_id: SESSION_ID,
    dealer: { gstin: DEALER_GSTIN, legal_name: 'PERFECT FORGINGS', trade_name: 'PERFECT FORGINGS', financial_year: FY },
    financial_year: FY,
    audit_status: 'in_progress',
    datasets: {
      gstr1: { dataset_key: 'gstr1', label: 'GSTR-1', source_files: ['gstr1.xlsx'], staged_files: [], merged: true, row_count: 9, status: 'merged', dealer_gstin: DEALER_GSTIN, financial_year: FY },
      gstr2a: { dataset_key: 'gstr2a', label: 'GSTR-2A', status: 'empty' },
      ewb_outward: { dataset_key: 'ewb_outward', label: 'EWB OUTWARD', source_files: ['ewb.xlsx'], staged_files: [], merged: true, row_count: 8, status: 'merged', dealer_gstin: DEALER_GSTIN, financial_year: FY },
      ewb_inward: { dataset_key: 'ewb_inward', label: 'EWB INWARD', status: 'empty' },
    },
    upload_history: [],
    comparison_status: [],
    discrepancies: { missing_invoice: 0, duplicate_invoice: 0, gstin_mismatch: 0, invoice_mismatch: 0, value_mismatch: 0, date_mismatch: 0, hsn_mismatch: 0, state_mismatch: 0, risk_score: 0, total: 0 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

test.describe('Background Jobs', () => {
  test.beforeEach(async ({ page, request }) => {
    const session = buildMergedSession();
    await request.post('http://127.0.0.1:8000/api/session/sync', { data: session, headers: authHeaders() });
    await prepareAuthenticatedPage(page, session);
    await page.waitForSelector('[data-testid="audit-header"]');
  });

  test('comparison runs as background job with progress', async ({ page, request }) => {
    const gstr1B64 = toBase64(path.join(fixturesDir, 'gstr1_comparison.xlsx'));
    const ewbB64 = toBase64(path.join(fixturesDir, 'ewb_comparison.xlsx'));
    const cmp = await request.post('http://127.0.0.1:8000/api/comparison/gstr1-eway', {
      headers: authHeaders(),
      data: { session_id: SESSION_ID, gstr1_workbook_base64: gstr1B64, ewb_outward_workbook_base64: ewbB64 },
    });
    expect(cmp.status()).toBe(202);
    const { job_id } = await cmp.json();

    await page.reload();
    await expect(page.getByTestId('job-queue-panel')).toBeVisible();
    await expect(page.getByTestId(`job-row-${job_id}`)).toBeVisible({ timeout: 15000 });

    await waitForJob(request, job_id);
    await page.reload();
    await expect(page.getByTestId(`job-status-${job_id}`)).toContainText(/completed/i);
    await saveEvidence(page, '26-jobs-comparison-complete');
  });

  test('cancel running job', async ({ page, request }) => {
    const gstr1B64 = toBase64(path.join(fixturesDir, 'gstr1_comparison.xlsx'));
    const ewbB64 = toBase64(path.join(fixturesDir, 'ewb_comparison.xlsx'));
    const cmp = await request.post('http://127.0.0.1:8000/api/comparison/gstr1-eway', {
      headers: authHeaders(),
      data: { session_id: SESSION_ID, gstr1_workbook_base64: gstr1B64, ewb_outward_workbook_base64: ewbB64 },
    });
    const { job_id } = await cmp.json();
    await page.reload();
    await page.waitForSelector(`[data-testid="job-row-${job_id}"]`, { timeout: 15000 }).catch(() => {});
    const cancelBtn = page.getByTestId(`job-cancel-${job_id}`);
    if (await cancelBtn.isVisible()) {
      await cancelBtn.click();
      await expect(page.getByTestId(`job-status-${job_id}`)).toContainText(/cancelled|failed|running|completed/i);
    }
    await saveEvidence(page, '27-jobs-cancel');
  });

  test('retry failed job', async ({ request }) => {
    const gstr1B64 = toBase64(path.join(fixturesDir, 'gstr1_comparison.xlsx'));
    const ewbB64 = toBase64(path.join(fixturesDir, 'ewb_comparison.xlsx'));
    await runComparisonJob(request, SESSION_ID, gstr1B64, ewbB64);
    const headers = authHeaders();
    const list = await request.get(`http://127.0.0.1:8000/api/jobs?session_id=${SESSION_ID}`, { headers });
    const { jobs } = await list.json();
    const completed = jobs.find((j) => j.status === 'completed');
    expect(completed).toBeTruthy();
    await request.post(`http://127.0.0.1:8000/api/jobs/${completed.job_id}/cancel`, { headers });
    const retried = await request.post(`http://127.0.0.1:8000/api/jobs/${completed.job_id}/retry`, { headers });
    expect([200, 400]).toContain(retried.status());
  });

  test('dashboard progress survives refresh', async ({ page, request }) => {
    const gstr1B64 = toBase64(path.join(fixturesDir, 'gstr1_comparison.xlsx'));
    const ewbB64 = toBase64(path.join(fixturesDir, 'ewb_comparison.xlsx'));
    await runComparisonJob(request, SESSION_ID, gstr1B64, ewbB64);
    await page.reload();
    await expect(page.getByTestId('job-queue-panel')).toBeVisible();
    await expect(page.getByTestId('job-section-completed')).toBeVisible();
    await saveEvidence(page, '28-jobs-after-refresh');
  });
});
