import { test, expect } from '@playwright/test';
import { saveEvidence } from './helpers/visualStability.js';
import { DEALER_GSTIN, FY, seedDashboardSession } from './helpers/dashboardSession.js';

test.describe('GST Audit Dashboard', () => {
  test.beforeEach(async ({ page, request }) => {
    await seedDashboardSession(page, request);
  });

  test('shows dealer header and readiness', async ({ page }) => {
    await expect(page.getByTestId('audit-header')).toContainText('PERFECT FORGINGS');
    await expect(page.getByTestId('audit-header')).toContainText(DEALER_GSTIN);
    await expect(page.getByTestId('audit-header')).toContainText(FY);
    await expect(page.getByTestId('readiness-panel')).toBeVisible();
    await saveEvidence(page, '01-dashboard-header');
  });

  test('shows four dataset status cards with record counts', async ({ page }) => {
    await expect(page.getByTestId('dataset-card-gstr1')).toBeVisible();
    await expect(page.getByTestId('dataset-card-gstr2a')).toBeVisible();
    await expect(page.getByTestId('dataset-card-ewb_outward')).toBeVisible();
    await expect(page.getByTestId('dataset-card-ewb_inward')).toBeVisible();
    await expect(page.getByTestId('dataset-card-gstr1')).toContainText('Rows Imported');
    await saveEvidence(page, '02-dashboard-dataset-cards');
  });

  test('shows FY calendar with sticky layout and record counts', async ({ page }) => {
    await expect(page.getByTestId('fy-calendar')).toBeVisible();
    await expect(page.getByTestId('calendar-header-gstr1')).toBeVisible();
    await expect(page.getByTestId('calendar-month-Apr')).toBeVisible();
    await expect(page.getByTestId('month-cell-gstr1-Apr')).toBeVisible();
    await expect(page.getByTestId('calendar-legend')).toContainText('Uploaded');
    await saveEvidence(page, '03-dashboard-fy-calendar-desktop');
  });

  test('opens month cell modal on click', async ({ page }) => {
    await page.getByTestId('month-cell-gstr1-Apr').click();
    await expect(page.getByTestId('month-cell-modal')).toBeVisible();
    await expect(page.getByTestId('month-cell-modal')).toContainText('GSTR-1');
    await saveEvidence(page, '04-dashboard-month-modal', { allowModal: true });
  });

  test('detects duplicate month uploads', async ({ page }) => {
    await expect(page.getByTestId('duplicate-panel')).toBeVisible();
    await expect(page.getByTestId('dup-action-gstr1-keep_latest')).toBeVisible();
    await expect(page.getByTestId('duplicate-detection')).toBeVisible();
    await saveEvidence(page, '05-dashboard-duplicates');
  });

  test('shows top summary, upload health, and statistics', async ({ page }) => {
    await expect(page.getByTestId('top-summary-panel')).toBeVisible();
    await expect(page.getByTestId('top-files')).toBeVisible();
    await expect(page.getByTestId('upload-health')).toBeVisible();
    await expect(page.getByTestId('summary-statistics')).toBeVisible();
    await expect(page.getByTestId('discrepancy-summary')).toBeVisible();
    await expect(page.getByTestId('discrepancy-missing_invoice')).toHaveText('0');
    await saveEvidence(page, '06-dashboard-statistics');
  });

  test('shows comparison status and audit not ready', async ({ page }) => {
    await expect(page.getByTestId('comparison-status')).toBeVisible();
    await expect(page.getByTestId('comparison-gstr1_ewb_outward')).toContainText(/not started/i);
    await expect(page.getByTestId('audit-not-ready')).toBeVisible();
    await saveEvidence(page, '07-dashboard-comparison-readiness');
  });

  test('shows upload history and workbook summary', async ({ page }) => {
    await expect(page.getByTestId('upload-history')).toBeVisible();
    await expect(page.getByTestId('upload-history')).toContainText('GSTR-1');
    await expect(page.getByTestId('workbook-summary')).toBeVisible();
    await saveEvidence(page, '08-dashboard-upload-history');
  });
});
