import { test, expect } from '@playwright/test';
import { saveEvidence } from './helpers/visualStability.js';
import { authHeaders, prepareAuthenticatedPage } from './helpers/auth.js';
import { buildTestSession } from './helpers/dashboardSession.js';

const SESSION = 'session_test_msae';

function buildMsaeSession() {
  return { ...buildTestSession(), session_id: SESSION };
}

test.describe('Audit Intelligence Center (MSAE)', () => {
  test.beforeEach(async ({ page, request }) => {
    const session = buildMsaeSession();
    await request.post('http://127.0.0.1:8000/api/session/sync', {
      headers: authHeaders(),
      data: session,
    });
    await prepareAuthenticatedPage(page, session);
  });

  test('shows consolidated audit intelligence dashboard', async ({ page }) => {
    await page.goto('/audit-intelligence');
    await expect(page.getByTestId('audit-intelligence-center')).toBeVisible();
    await expect(page.getByTestId('msae-score-cards')).toBeVisible();
    await expect(page.getByTestId('msae-master-cases-panel')).toBeVisible();
    await expect(page.getByTestId('msae-dealer-risk')).toBeVisible();
    await saveEvidence(page, '25-audit-report-intelligence');
  });

  test('navigation includes audit intelligence link', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Audit Intelligence' })).toBeVisible();
  });

  test('orchestrate button triggers refresh', async ({ page }) => {
    await page.goto('/audit-intelligence');
    await expect(page.getByTestId('msae-refresh')).toBeEnabled();
    await page.getByTestId('msae-refresh').click();
    await expect(page.getByTestId('msae-master-cases-panel')).toBeVisible();
  });
});
