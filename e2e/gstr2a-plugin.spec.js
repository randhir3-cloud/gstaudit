import { test, expect } from '@playwright/test';
import { authHeaders } from './helpers/auth.js';

const SESSION_ID = 'session_gstr2a_e2e';

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
    comparison_status: [{ id: 'gstr2a_ewb_inward', label: 'GSTR-2A ↔ EWB INWARD', left_dataset: 'gstr2a', right_dataset: 'ewb_inward', status: 'ready' }],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

test.describe('GSTR-2A Plugin', () => {
  test.beforeEach(async ({ request }) => {
    await request.post('http://127.0.0.1:8000/api/session/sync', {
      data: buildSession(),
      headers: authHeaders(),
    });
  });

  test('plugin catalog lists gstr2a comparison pair', async ({ request }) => {
    const res = await request.get('http://127.0.0.1:8000/api/plugins', { headers: authHeaders() });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const plugin = body.plugins.find((p) => p.id === 'gstr2a');
    expect(plugin).toBeTruthy();
    expect(plugin.comparisons.some((c) => c.comparison_id === 'gstr2a_ewb_inward')).toBeTruthy();
    expect(body.comparison_pairs.some((c) => c.comparison_id === 'gstr2a_ewb_inward')).toBeTruthy();
  });

  test('comparison endpoint accepts gstr2a job enqueue', async ({ request }) => {
    const res = await request.post('http://127.0.0.1:8000/api/comparison/gstr2a-eway', {
      headers: authHeaders(),
      data: { session_id: SESSION_ID },
    });
    expect(res.status()).toBe(202);
    const body = await res.json();
    expect(body.comparison_id).toBe('gstr2a_ewb_inward');
    expect(body.job_id).toBeTruthy();
  });

  test('report section endpoint returns purchase reconciliation', async ({ request }) => {
    const res = await request.get('http://127.0.0.1:8000/api/plugins/gstr2a/report-section', {
      headers: authHeaders(),
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.section.title).toBe('Purchase Reconciliation');
  });
});
