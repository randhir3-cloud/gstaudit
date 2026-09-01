import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { saveEvidence } from './helpers/visualStability.js';
import { runComparisonJob } from './helpers/jobs.js';
import { authHeaders, prepareAuthenticatedPage } from './helpers/auth.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');

const SESSION_ID = 'session_comparison_e2e';
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

test.describe('GSTR-1 vs EWB Comparison Engine', () => {
  test.beforeEach(async ({ page, request }) => {
    const session = buildMergedSession();
    await request.post('http://127.0.0.1:8000/api/session/sync', { data: session, headers: authHeaders() });
    const gstr1B64 = toBase64(path.join(fixturesDir, 'gstr1_comparison.xlsx'));
    const ewbB64 = toBase64(path.join(fixturesDir, 'ewb_comparison.xlsx'));
    await runComparisonJob(request, SESSION_ID, gstr1B64, ewbB64);
    await prepareAuthenticatedPage(page, session);
    await page.waitForSelector('[data-testid="audit-header"]');
  });

  test('dashboard shows completed comparison and discrepancies', async ({ page }) => {
    await expect(page.getByTestId('comparison-gstr1_ewb_outward')).toContainText(/completed/i);
    await expect(page.getByTestId('discrepancy-missing_invoice')).not.toHaveText('0');
    await expect(page.getByTestId('discrepancy-risk_score')).not.toHaveText('0');
    await saveEvidence(page, '12-comparison-dashboard');
  });

  test('comparison screen shows summary and risk', async ({ page }) => {
    await page.goto('/comparison');
    await expect(page.getByTestId('comparison-summary-panel')).toBeVisible();
    await expect(page.getByTestId('comparison-run-status')).toContainText(/completed/i);
    await expect(page.getByTestId('cmp-matched')).toBeVisible();
    await expect(page.getByTestId('cmp-risk-score')).not.toHaveText('0');
    await expect(page.getByTestId('comparison-observations')).toBeVisible();
    await saveEvidence(page, '13-comparison-summary');
  });

  test('detail view opens filtered missing invoice table', async ({ page }) => {
    await page.goto('/workbook?filter=MISSING_IN_GSTR1');
    await expect(page.getByTestId('comparison-detail-table')).toBeVisible();
    await expect(page.getByTestId('workbook-row-0')).toBeVisible();
    await saveEvidence(page, '14-comparison-detail-missing');
  });

  test('detail view for value mismatch', async ({ page }) => {
    await page.goto('/workbook?filter=VALUE_MISMATCH');
    await expect(page.getByTestId('comparison-detail-table')).toBeVisible();
    await saveEvidence(page, '15-comparison-detail-value');
  });

  test('dashboard discrepancy link navigates to detail', async ({ page }) => {
    await page.getByTestId('discrepancy-link-missing_invoice').click();
    await expect(page.getByTestId('comparison-detail-table')).toBeVisible();
    await saveEvidence(page, '16-comparison-discrepancy-link');
  });
});
