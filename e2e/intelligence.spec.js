import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { saveEvidence } from './helpers/visualStability.js';
import { runComparisonJob } from './helpers/jobs.js';
import { authHeaders, prepareAuthenticatedPage } from './helpers/auth.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');
const SESSION_ID = 'session_intelligence_e2e';
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

async function seedSession(request) {
  const session = buildMergedSession();
  expect((await request.post('http://127.0.0.1:8000/api/session/sync', { data: session, headers: authHeaders() })).ok()).toBeTruthy();
  await runComparisonJob(
    request,
    SESSION_ID,
    toBase64(path.join(fixturesDir, 'gstr1_comparison.xlsx')),
    toBase64(path.join(fixturesDir, 'ewb_comparison.xlsx')),
  );
  const intel = await request.get(`http://127.0.0.1:8000/api/intelligence/summary?session_id=${SESSION_ID}`, { headers: authHeaders() });
  expect(intel.ok()).toBeTruthy();
  const body = await intel.json();
  expect(body.cards).toBeDefined();
  return session;
}

test.describe('Audit Intelligence Layer', () => {
  test.beforeEach(async ({ page, request }) => {
    const session = await seedSession(request);
    await prepareAuthenticatedPage(page, session);
    await page.waitForSelector('[data-testid="audit-header"]');
  });

  test('dashboard shows audit intelligence cards', async ({ page }) => {
    await page.waitForSelector('[data-testid="audit-intelligence-panel"]', { timeout: 15000 });
    await expect(page.getByTestId('intel-high-risk-cases')).toBeVisible();
    await expect(page.getByTestId('intel-critical-suppliers')).toBeVisible();
    await expect(page.getByTestId('intel-heatmap-months')).toBeVisible();
    await saveEvidence(page, '22-audit-intelligence-dashboard');
  });

  test('dashboard shows patterns and recommendations', async ({ page }) => {
    await page.waitForSelector('[data-testid="audit-intelligence-panel"]');
    await expect(page.getByTestId('intel-patterns')).toBeVisible();
    await saveEvidence(page, '23-audit-intelligence-patterns');
  });

  test('investigation case shows priority and documents', async ({ page }) => {
    await page.goto('/investigation');
    await page.waitForSelector('[data-testid="investigation-row-0"]');
    await page.getByTestId('investigation-row-0').click();
    await expect(page.getByTestId('case-priority-badge')).toBeVisible();
    await expect(page.getByTestId('case-recommended-documents')).toBeVisible();
    await expect(page.getByTestId('case-suggested-verification')).toBeVisible();
    await saveEvidence(page, '24-investigation-intelligence-case');
  });

  test('audit report shows intelligence section', async ({ page }) => {
    await page.goto('/audit-report');
    await page.waitForSelector('[data-testid="report-preview"]');
    await page.waitForSelector('[data-testid="report-intelligence-section"]', { timeout: 15000 });
    await expect(page.getByTestId('report-suggested-documents')).toBeVisible();
    await saveEvidence(page, '25-audit-report-intelligence');
  });
});
