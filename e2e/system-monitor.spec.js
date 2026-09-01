import { test, expect } from '@playwright/test';
import { authHeaders, prepareAuthenticatedPage } from './helpers/auth.js';

test.describe('System Monitor', () => {
  test.beforeEach(async ({ page }) => {
    await prepareAuthenticatedPage(page);
  });

  test('system dashboard loads health cards and metrics', async ({ page, request }) => {
    const healthRes = await request.get('http://127.0.0.1:8000/api/system/health', { headers: authHeaders() });
    expect(healthRes.ok()).toBeTruthy();
    const metricsRes = await request.get('http://127.0.0.1:8000/api/system/metrics', { headers: authHeaders() });
    expect(metricsRes.ok()).toBeTruthy();

    await page.goto('/system-monitor');
    await expect(page.getByTestId('system-monitor-header')).toBeVisible();
    await expect(page.getByTestId('system-health-cards')).toBeVisible();
    await expect(page.getByTestId('health-card-application')).toBeVisible();
    await expect(page.getByTestId('health-card-database')).toBeVisible();
    await expect(page.getByTestId('system-database-panel')).toBeVisible();
    await expect(page.getByTestId('system-jobs-panel')).toBeVisible();
    await expect(page.getByTestId('system-users-panel')).toBeVisible();
    await expect(page.getByTestId('system-performance-panel')).toBeVisible();
  });

  test('logs panel supports filter and export', async ({ page, request }) => {
    await page.goto('/system-monitor');
    await expect(page.getByTestId('system-logs-panel')).toBeVisible();
    await expect(page.getByTestId('system-logs-list')).toBeVisible();
    await page.getByTestId('logs-source-filter').selectOption('security');
    await page.getByTestId('logs-filter-button').click();
    const exportRes = await request.get('http://127.0.0.1:8000/api/system/logs/export?limit=10', { headers: authHeaders() });
    expect(exportRes.ok()).toBeTruthy();
    const body = await exportRes.text();
    expect(body).toContain('timestamp,source,level,user,action,message,session_id,result');
  });

  test('responsive layout on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 810, height: 1080 });
    await page.goto('/system-monitor');
    await expect(page.getByTestId('system-monitor-layout')).toBeVisible();
    await expect(page.getByTestId('system-health-cards')).toBeVisible();
  });

  test('dark mode renders monitor panels', async ({ page }) => {
    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    });
    await page.goto('/system-monitor');
    await expect(page.getByTestId('health-overall')).toBeVisible();
    await expect(page.getByTestId('system-config-panel')).toBeVisible();
    const dark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    expect(dark).toBeTruthy();
  });
});
