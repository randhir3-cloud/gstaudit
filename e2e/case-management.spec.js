import { test, expect } from '@playwright/test';
import { saveEvidence } from './helpers/visualStability.js';
import { authHeaders, prepareAuthenticatedPage } from './helpers/auth.js';
import { buildTestSession } from './helpers/dashboardSession.js';

const SESSION = 'session_test_case_mgmt';

async function seedSession(request, page) {
  const session = { ...buildTestSession(), session_id: SESSION };
  await request.post('http://127.0.0.1:8000/api/session/sync', {
    headers: authHeaders(),
    data: session,
  });
  await request.post(`http://127.0.0.1:8000/api/audit-cases/dev/seed-demo?session_id=${SESSION}`, {
    headers: authHeaders(),
  });
  await prepareAuthenticatedPage(page, session);
}

async function resetCases(request) {
  await request.post(`http://127.0.0.1:8000/api/audit-cases/reset?session_id=${SESSION}`, {
    headers: authHeaders(),
  });
}

async function assignFirstCaseViaApi(request) {
  const list = await request.get(`http://127.0.0.1:8000/api/audit-cases?session_id=${SESSION}`, {
    headers: authHeaders(),
  });
  const cases = (await list.json()).cases || [];
  if (!cases.length) return null;
  const caseId = cases[0].audit_case_id;
  await request.post(`http://127.0.0.1:8000/api/audit-cases/${caseId}/assign`, {
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    data: {
      session_id: SESSION,
      assigned_officer: 'test_officer',
      assigned_supervisor: 'supervisor',
      due_date: '2026-12-31',
    },
  });
  await request.post(`http://127.0.0.1:8000/api/audit-cases/${caseId}/transition`, {
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    data: {
      session_id: SESSION,
      to_status: 'Under Investigation',
      actor: 'test_officer',
    },
  });
  return caseId;
}

test.describe('Audit Case Management Workflow', () => {
  test.beforeEach(async ({ page, request }) => {
    await seedSession(request, page);
    await resetCases(request);
  });

  test('loads case management with cases from MSAE', async ({ page }) => {
    await page.goto('/audit-cases');
    await expect(page.getByTestId('audit-case-management')).toBeVisible();
    await expect(page.locator('[data-testid^="audit-case-row-"]').first()).toBeVisible();
    await saveEvidence(page, 'case-management-list');
  });

  test('assigns case and transitions workflow', async ({ page }) => {
    await page.goto('/audit-cases');
    await page.locator('[data-testid^="audit-case-row-"]').first().click();
    await expect(page.getByTestId('assign-form')).toBeVisible();
    await page.getByTestId('assign-officer').fill('test_officer');
    await page.getByTestId('assign-due-date').fill('2026-12-31');
    const assignResp = page.waitForResponse((r) => r.url().includes('/assign') && r.status() === 200);
    await page.getByTestId('assign-submit').click();
    await assignResp;
    await expect(page.getByTestId('transition-actions')).toBeVisible({ timeout: 10000 });
    await page.getByTestId('transition-Under-Investigation').click();
    await saveEvidence(page, 'case-assigned-investigation');
  });

  test('generates notice during investigation', async ({ page, request }) => {
    await assignFirstCaseViaApi(request);
    await page.goto('/audit-cases');
    await page.locator('[data-testid^="audit-case-row-"]').first().click();
    await page.getByTestId('generate-notice').click();
    await expect(page.getByTestId('case-notices')).toBeVisible({ timeout: 10000 });
    await saveEvidence(page, 'case-notice-issued');
  });

  test('officer tasks page shows task counts', async ({ page }) => {
    await page.goto('/officer-tasks');
    await expect(page.getByTestId('officer-tasks-page')).toBeVisible();
    await expect(page.getByTestId('task-counts')).toBeVisible();
  });

  test('supervisor dashboard loads', async ({ page }) => {
    await page.goto('/supervisor-dashboard');
    await expect(page.getByTestId('supervisor-dashboard')).toBeVisible();
    await expect(page.getByTestId('supervisor-metrics')).toBeVisible();
  });

  test('case timeline shows events after actions', async ({ page, request }) => {
    await assignFirstCaseViaApi(request);
    await page.goto('/audit-cases');
    await page.locator('[data-testid^="audit-case-row-"]').first().click();
    await expect(page.getByTestId('case-timeline')).toBeVisible();
    await expect(page.getByTestId('case-timeline').locator('li').first()).toBeVisible();
  });
});
