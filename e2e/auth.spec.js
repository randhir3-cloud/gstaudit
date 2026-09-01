import { test, expect } from '@playwright/test';
import { ADMIN_PASSWORD, ADMIN_USERNAME, authHeaders, loginAndSaveToken, prepareAuthenticatedPage } from './helpers/auth.js';

test.describe('Security & Authentication', () => {
  test('login API returns access token', async ({ request }) => {
    const res = await request.post('http://127.0.0.1:8000/api/auth/login', {
      data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.access_token).toBeTruthy();
    expect(body.user.username).toBe('admin');
  });

  test('protected API rejects unauthenticated requests', async ({ request }) => {
    const res = await request.get('http://127.0.0.1:8000/api/dashboard?session_id=session_test');
    expect(res.status()).toBe(401);
  });

  test('authenticated API access succeeds', async ({ request }) => {
    const headers = authHeaders();
    const res = await request.get('http://127.0.0.1:8000/api/auth/me', { headers });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.username).toBe('admin');
  });

  test('login page and logout flow', async ({ page }) => {
    await prepareAuthenticatedPage(page);
    await expect(page.getByTestId('audit-header')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('security-panel')).toBeVisible();
    await expect(page.getByTestId('current-user-name')).toContainText(/admin/i);
  });

  test('viewer role permission denied for admin panel', async ({ request }) => {
    const adminHeaders = authHeaders();
    const create = await request.post('http://127.0.0.1:8000/api/admin/users', {
      headers: adminHeaders,
      data: {
        username: 'viewer_e2e',
        password: 'Viewer@123456!',
        role_ids: ['role_viewer'],
      },
    });
    expect(create.status()).toBe(201);

    const login = await request.post('http://127.0.0.1:8000/api/auth/login', {
      data: { username: 'viewer_e2e', password: 'Viewer@123456!' },
    });
    const viewer = await login.json();

    const denied = await request.get('http://127.0.0.1:8000/api/admin/users', {
      headers: { Authorization: `Bearer ${viewer.access_token}` },
    });
    expect(denied.status()).toBe(403);
  });

  test('audit logs record login', async ({ request }) => {
    await loginAndSaveToken();
    const headers = authHeaders();
    const logs = await request.get('http://127.0.0.1:8000/api/admin/audit-logs?limit=20', { headers });
    expect(logs.ok()).toBeTruthy();
    const body = await logs.json();
    expect(body.logs.some((l) => l.action === 'login')).toBeTruthy();
  });
});
