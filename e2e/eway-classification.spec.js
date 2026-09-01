import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { saveEvidence } from './helpers/visualStability.js';
import { prepareAuthenticatedPage } from './helpers/auth.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');
const evidenceDir = path.join(__dirname, '..', 'docs', 'evidence');

const DEALER_GSTIN = fs.readFileSync(path.join(fixturesDir, 'dealer_gstin.txt'), 'utf8').trim();

async function openEwayTab(page, subTab = 'outward') {
  await page.goto('/merge');
  await page.getByTestId('merge-tab-eway').click();
  if (subTab === 'inward') {
    await page.getByTestId('eway-tab-inward').click();
  } else {
    await page.getByTestId('eway-tab-outward').click();
  }
}

async function ensureDealerGstin(page) {
  const modal = page.getByTestId('dealer-gstin-modal');
  const appeared = await modal.waitFor({ state: 'visible', timeout: 5000 }).then(() => true).catch(() => false);
  if (!appeared) return;

  const secondClassify = page.waitForResponse(
    (res) => res.url().includes('/api/eway/classify'),
    { timeout: 15_000 },
  );
  await page.getByTestId('dealer-gstin-input').fill(DEALER_GSTIN);
  await page.getByTestId('dealer-gstin-submit').click();
  await secondClassify;
  await expect(modal).toBeHidden({ timeout: 10_000 });
}

async function uploadFixture(page, filename) {
  const filePath = path.join(fixturesDir, filename);
  const classifyResponse = page.waitForResponse(
    (res) => res.url().includes('/api/eway/classify'),
    { timeout: 15_000 },
  );
  const input = page.getByTestId('eway-file-input');
  await input.evaluate((el) => {
    el.value = '';
  });
  await input.setInputFiles(filePath);
  const response = await classifyResponse;
  expect(response.ok()).toBeTruthy();
  await ensureDealerGstin(page);
}

async function establishDealerGstin(page) {
  await openEwayTab(page, 'outward');
  await uploadFixture(page, 'outward_correct.xlsx');
  await expect(page.getByTestId('eway-validation-table')).toBeVisible({ timeout: 15_000 });
  await page.getByRole('button', { name: 'Clear All' }).click();
  await expect(page.getByTestId('eway-validation-table')).toHaveCount(0);
}

test.describe('Intelligent E-Way Bill Classification', () => {
  test.beforeAll(() => {
    fs.mkdirSync(evidenceDir, { recursive: true });
  });

  test.beforeEach(async ({ page }) => {
    await prepareAuthenticatedPage(page);
    await establishDealerGstin(page);
  });

  test('correct outward upload on outward tab', async ({ page }) => {
    await uploadFixture(page, 'outward_correct.xlsx');

    const table = page.getByTestId('eway-validation-table');
    await expect(table).toBeVisible();
    await expect(table).toContainText(/outward/i);
    await expect(table).toContainText('100%');
    await expect(table).toContainText(DEALER_GSTIN);
    await expect(table).toContainText('valid');

    await saveEvidence(page, '01-correct-outward-upload', { dir: evidenceDir });
  });

  test('correct inward upload on inward tab', async ({ page }) => {
    await page.getByTestId('eway-tab-inward').click();
    await uploadFixture(page, 'inward_correct.xlsx');

    const table = page.getByTestId('eway-validation-table');
    await expect(table).toBeVisible();
    await expect(table).toContainText(/inward/i);
    await expect(table).toContainText('100%');
    await expect(table).toContainText('valid');

    await saveEvidence(page, '02-correct-inward-upload', { dir: evidenceDir });
  });

  test('wrong upload shows dialog and auto-move to correct section', async ({ page }) => {
    await page.getByTestId('eway-tab-inward').click();
    await uploadFixture(page, 'outward_for_wrong_section.xlsx');

    const dialog = page.getByTestId('wrong-upload-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText(/outward/i);
    await expect(dialog).toContainText('Move Automatically');

    await saveEvidence(page, '03-wrong-upload-dialog', { allowModal: true, dir: evidenceDir });

    await page.getByTestId('wrong-upload-move').click();
    await expect(dialog).toBeHidden();
    await expect(page.getByTestId('eway-tab-outward')).toHaveAttribute('class', /text-blue-600/);

    const table = page.getByTestId('eway-validation-table');
    await expect(table).toBeVisible();
    await expect(table).toContainText(/outward/i);
    await expect(table).toContainText('valid');

    await saveEvidence(page, '04-wrong-upload-auto-moved', { dir: evidenceDir });
  });

  test('wrong upload cancel keeps file out of merge list', async ({ page }) => {
    await page.getByTestId('eway-tab-outward').click();
    await uploadFixture(page, 'inward_correct.xlsx');

    const dialog = page.getByTestId('wrong-upload-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText(/inward/i);

    await page.getByTestId('wrong-upload-cancel').click();
    await expect(dialog).toBeHidden();
    await expect(page.getByTestId('eway-validation-table')).toHaveCount(0);

    await saveEvidence(page, '05-wrong-upload-cancelled', { dir: evidenceDir });
  });

  test('mixed upload is rejected as unknown', async ({ page }) => {
    await page.getByTestId('eway-tab-outward').click();
    await uploadFixture(page, 'mixed_unknown.xlsx');

    await expect(page.getByText(/Error:.*mixed_unknown\.xlsx/i)).toBeVisible();
    await expect(page.getByTestId('eway-validation-table')).toHaveCount(0);

    await saveEvidence(page, '06-mixed-unknown-upload', { dir: evidenceDir });
  });

  test('ambiguous upload is rejected as unknown', async ({ page }) => {
    await page.getByTestId('eway-tab-inward').click();
    await uploadFixture(page, 'ambiguous_unknown.xlsx');

    await expect(page.getByText(/Error:.*ambiguous_unknown\.xlsx/i)).toBeVisible();
    await expect(page.getByTestId('eway-validation-table')).toHaveCount(0);

    await saveEvidence(page, '07-ambiguous-unknown-upload', { dir: evidenceDir });
  });
});
