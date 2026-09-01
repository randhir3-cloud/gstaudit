import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { saveEvidence } from './helpers/visualStability.js';
import { runComparisonJob } from './helpers/jobs.js';
import { authHeaders, prepareAuthenticatedPage } from './helpers/auth.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');
const SESSION_ID = 'session_investigation_e2e';
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

async function seedComparison(request) {
  const session = buildMergedSession();
  const sync = await request.post('http://127.0.0.1:8000/api/session/sync', { data: session, headers: authHeaders() });
  expect(sync.ok()).toBeTruthy();
  await runComparisonJob(
    request,
    SESSION_ID,
    toBase64(path.join(fixturesDir, 'gstr1_comparison.xlsx')),
    toBase64(path.join(fixturesDir, 'ewb_comparison.xlsx')),
  );
  const inv = await request.get(`http://127.0.0.1:8000/api/investigation?session_id=${SESSION_ID}&limit=200`, { headers: authHeaders() });
  expect(inv.ok()).toBeTruthy();
  const invBody = await inv.json();
  expect(invBody.summary.total).toBeGreaterThan(0);
  return session;
}

test.describe('Audit Investigation Workbench', () => {
  test.beforeEach(async ({ page, request }) => {
    const session = await seedComparison(request);
    await prepareAuthenticatedPage(page, session);
    await page.waitForSelector('[data-testid="audit-header"]');
  });

  test('opens investigation workbench', async ({ page }) => {
    await page.goto('/investigation');
    await expect(page.getByTestId('investigation-categories')).toBeVisible();
    await expect(page.getByTestId('investigation-grid')).toBeVisible();
    await expect(page.getByTestId('category-ALL')).not.toHaveText(/0$/);
    await saveEvidence(page, '17-investigation-workbench');
  });

  test('opens case and adds remark', async ({ page }) => {
    await page.goto('/investigation');
    await page.waitForSelector('[data-testid="investigation-row-0"]', { timeout: 15000 });
    await page.getByTestId('investigation-row-0').click();
    await expect(page.getByTestId('investigation-details')).toBeVisible();
    await page.getByTestId('case-remarks-input').fill('Verified against sales register.');
    await page.getByTestId('case-status-select').selectOption('Verified');
    await page.getByTestId('save-case-btn').click();
    await expect(page.getByTestId('investigation-details')).toBeVisible();
    await saveEvidence(page, '18-investigation-case-remark');
  });

  test('bulk mark verified', async ({ page }) => {
    await page.goto('/investigation');
    await page.waitForSelector('[data-testid="investigation-row-0"]', { timeout: 15000 });
    await page.locator('[data-testid="investigation-row-0"] input[type="checkbox"]').check();
    await page.locator('[data-testid="investigation-row-1"] input[type="checkbox"]').check();
    await page.getByTestId('bulk-verify').click();
    await saveEvidence(page, '19-investigation-bulk');
  });

  test('dashboard shows case tracking', async ({ page }) => {
    await page.waitForSelector('[data-testid="case-tracking-panel"]', { timeout: 15000 });
    await expect(page.getByTestId('case-tracking-panel')).toBeVisible();
    await expect(page.getByTestId('cases-open')).not.toHaveText('0');
    await saveEvidence(page, '20-dashboard-case-tracking');
  });

  test('generate PDF Excel Word reports', async ({ page, request }) => {
    await prepareAuthenticatedPage(page);
    await page.goto('/audit-report');
    await page.waitForSelector('[data-testid="report-preview"]', { timeout: 15000 });
    await expect(page.getByTestId('report-preview')).toBeVisible();
    await expect(page.getByTestId('preview-dealer')).toBeVisible();
    for (const format of ['pdf', 'excel', 'docx']) {
      const headers = authHeaders();
      const res = await request.post(`http://127.0.0.1:8000/api/report/generate?session_id=${SESSION_ID}&format=${format}`, { headers });
      expect(res.status()).toBe(202);
      const { job_id } = await res.json();
      const jobRes = await request.get(`http://127.0.0.1:8000/api/jobs/${job_id}`, { headers });
      expect(jobRes.ok()).toBeTruthy();
      const job = await jobRes.json();
      let status = job.status;
      const start = Date.now();
      while (status !== 'completed' && Date.now() - start < 60000) {
        await new Promise((r) => setTimeout(r, 500));
        const polled = await (await request.get(`http://127.0.0.1:8000/api/jobs/${job_id}`, { headers })).json();
        status = polled.status;
      }
      expect(status).toBe('completed');
      const dl = await request.get(`http://127.0.0.1:8000/api/jobs/${job_id}/download`, { headers });
      expect(dl.ok()).toBeTruthy();
    }
    await saveEvidence(page, '21-audit-report-preview');
  });
});
