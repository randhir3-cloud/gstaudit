import { test, expect } from '@playwright/test';
import { authHeaders, readAuthToken } from './helpers/auth.js';
import { waitForJob, waitForJobType } from './helpers/jobs.js';
import { GSTR2A_COMPARISON_B64, PURCHASE_REGISTER_B64 } from './fixtures/purchaseRegister.js';

const SESSION_ID = 'session_purchase_e2e';

function buildSession() {
  return {
    session_id: SESSION_ID,
    dealer: { gstin: '03AABCU9603R1ZX', legal_name: 'PERFECT FORGINGS', trade_name: 'PERFECT FORGINGS', financial_year: '2023-24' },
    financial_year: '2023-24',
    audit_status: 'in_progress',
    datasets: {
      gstr2a: { dataset_key: 'gstr2a', label: 'GSTR-2A', merged: true, row_count: 3, status: 'merged' },
      ewb_inward: { dataset_key: 'ewb_inward', label: 'EWB INWARD', merged: true, row_count: 3, status: 'merged' },
    },
    comparison_status: [
      { id: 'purchase_register_vs_gstr2a', label: 'Purchase Register ↔ GSTR-2A', left_dataset: 'purchase_register', right_dataset: 'gstr2a', status: 'ready' },
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

test.describe('Purchase Register Plugin', () => {
  test.beforeEach(async ({ request }) => {
    await request.post('http://127.0.0.1:8000/api/session/sync', {
      data: buildSession(),
      headers: authHeaders(),
    });
  });

  test('plugin catalog lists purchase comparisons', async ({ request }) => {
    const res = await request.get('http://127.0.0.1:8000/api/plugins', { headers: authHeaders() });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const plugin = body.plugins.find((p) => p.id === 'purchase');
    expect(plugin).toBeTruthy();
    expect(plugin.comparisons.some((c) => c.comparison_id === 'purchase_register_vs_gstr2a')).toBeTruthy();
    expect(body.comparison_pairs.some((c) => c.comparison_id === 'purchase_register_vs_gstr2a')).toBeTruthy();
  });

  test('import preview detects columns from workbook', async ({ request }) => {
    const res = await request.post('http://127.0.0.1:8000/api/purchase/import/preview', {
      headers: authHeaders(),
      data: { file_base64: PURCHASE_REGISTER_B64, filename: 'purchase.xlsx' },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.row_count).toBe(3);
    expect(body.detected_mapping.invoice_number).toBeTruthy();
  });

  test('comparison endpoint enqueues purchase vs gstr2a job', async ({ request }) => {
    await request.post('http://127.0.0.1:8000/api/purchase/import', {
      headers: authHeaders(),
      data: { session_id: SESSION_ID, file_base64: PURCHASE_REGISTER_B64, filename: 'purchase.xlsx' },
    });
    const res = await request.post('http://127.0.0.1:8000/api/comparison/purchase-gstr2a', {
      headers: authHeaders(),
      data: {
        session_id: SESSION_ID,
        purchase_register_workbook_base64: PURCHASE_REGISTER_B64,
        gstr2a_workbook_base64: GSTR2A_COMPARISON_B64,
      },
    });
    expect(res.status()).toBe(202);
    const body = await res.json();
    expect(body.comparison_id).toBe('purchase_register_vs_gstr2a');
    expect(body.job_id).toBeTruthy();
  });

  test('report section endpoint returns purchase register reconciliation', async ({ request }) => {
    const res = await request.get('http://127.0.0.1:8000/api/plugins/purchase/report-section', {
      headers: authHeaders(),
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.section.title).toBe('Purchase Register Reconciliation');
  });

  test('import workbench UI loads', async ({ page }) => {
    const token = readAuthToken();
    await page.setExtraHTTPHeaders({ Authorization: `Bearer ${token}` });
    const res = await page.goto('http://127.0.0.1:8000/api/purchase/ui');
    expect(res?.ok()).toBeTruthy();
    await expect(page.getByTestId('purchase-import-workbench')).toBeVisible();
    await expect(page.getByTestId('purchase-preview-btn')).toBeVisible();
  });

  test('full flow: import, compare, MSAE orchestrate', async ({ request }) => {
    const importRes = await request.post('http://127.0.0.1:8000/api/purchase/import', {
      headers: authHeaders(),
      data: { session_id: SESSION_ID, file_base64: PURCHASE_REGISTER_B64, filename: 'purchase.xlsx' },
    });
    expect(importRes.ok()).toBeTruthy();

    const cmp = await request.post('http://127.0.0.1:8000/api/comparison/purchase-gstr2a', {
      headers: authHeaders(),
      data: {
        session_id: SESSION_ID,
        purchase_register_workbook_base64: PURCHASE_REGISTER_B64,
        gstr2a_workbook_base64: GSTR2A_COMPARISON_B64,
      },
    });
    expect(cmp.status()).toBe(202);
    const { job_id } = await cmp.json();
    await waitForJob(request, job_id);
    await waitForJobType(request, SESSION_ID, 'intelligence');

    const msae = await request.post(`http://127.0.0.1:8000/api/msae/orchestrate?session_id=${SESSION_ID}`, {
      headers: authHeaders(),
    });
    expect(msae.ok()).toBeTruthy();
    const msaeBody = await msae.json();
    expect(msaeBody.sources_analyzed).toContain('purchase_register_vs_gstr2a');

    const cases = await request.get(`http://127.0.0.1:8000/api/investigation?session_id=${SESSION_ID}&limit=50`, {
      headers: authHeaders(),
    });
    expect(cases.ok()).toBeTruthy();
    const caseBody = await cases.json();
    expect(caseBody.summary.total).toBeGreaterThan(0);
  });
});
