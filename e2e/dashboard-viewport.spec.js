import { test, expect } from '@playwright/test';
import { saveEvidence } from './helpers/visualStability.js';
import { seedDashboardSession } from './helpers/dashboardSession.js';

const VIEWPORTS = [
  {
    name: 'tablet',
    width: 810,
    height: 1080,
    calendarEvidence: '09-dashboard-tablet',
  },
  {
    name: 'mobile',
    width: 390,
    height: 844,
    calendarEvidence: '10-dashboard-mobile',
    modalEvidence: '11-dashboard-mobile-modal',
  },
];

for (const viewport of VIEWPORTS) {
  test.describe(`GST Audit Dashboard — Responsive (${viewport.name})`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test.beforeEach(async ({ page, request }) => {
      await seedDashboardSession(page, request);
    });

    test('responsive layout renders calendar and summary', async ({ page }) => {
      await expect(page.getByTestId('fy-calendar')).toBeVisible();
      await expect(page.getByTestId('top-summary-panel')).toBeVisible();
      await expect(page.getByTestId('calendar-month-Apr')).toBeVisible();
      await saveEvidence(page, viewport.calendarEvidence);
    });

    test('month modal on viewport', async ({ page }) => {
      await page.getByTestId('month-cell-gstr1-Apr').click();
      await expect(page.getByTestId('month-cell-modal')).toBeVisible();
      if (viewport.modalEvidence) {
        await saveEvidence(page, viewport.modalEvidence, { allowModal: true });
      }
    });
  });
}
