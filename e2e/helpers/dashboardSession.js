import { expect } from '@playwright/test';
import { authHeaders, prepareAuthenticatedPage } from './auth.js';

export const DEALER_GSTIN = '03AABCU9603R1ZX';
export const FY = '2023-24';

export function buildTestSession() {
  const filenames = [
    `GSTR1_${DEALER_GSTIN}_042023_R1.xlsx`,
    `GSTR1_${DEALER_GSTIN}_052023_R1.xlsx`,
    `GSTR1_${DEALER_GSTIN}_072023_R1.xlsx`,
    `GSTR1_${DEALER_GSTIN}_042023_R1_dup.xlsx`,
  ];
  return {
    session_id: 'session_test_dashboard',
    dealer: {
      gstin: DEALER_GSTIN,
      legal_name: 'PERFECT FORGINGS',
      trade_name: 'PERFECT FORGINGS',
      financial_year: FY,
    },
    financial_year: FY,
    audit_status: 'in_progress',
    datasets: {
      gstr1: {
        dataset_key: 'gstr1',
        label: 'GSTR-1',
        source_files: [],
        staged_files: filenames,
        merged: false,
        row_count: 50200,
        status: 'uploaded',
        dealer_gstin: DEALER_GSTIN,
        financial_year: FY,
      },
      gstr2a: { dataset_key: 'gstr2a', label: 'GSTR-2A', status: 'empty' },
      ewb_outward: { dataset_key: 'ewb_outward', label: 'EWB OUTWARD', status: 'empty' },
      ewb_inward: { dataset_key: 'ewb_inward', label: 'EWB INWARD', status: 'empty' },
    },
    upload_history: filenames.map((f, i) => ({
      timestamp: new Date().toISOString(),
      dataset: 'gstr1',
      dataset_label: 'GSTR-1',
      filename: f,
      rows: 12550 + i,
      status: 'uploaded',
    })),
    comparison_status: [],
    discrepancies: {
      missing_invoice: 0, duplicate_invoice: 0, gstin_mismatch: 0,
      invoice_mismatch: 0, value_mismatch: 0, date_mismatch: 0,
      hsn_mismatch: 0, state_mismatch: 0, risk_score: 0, total: 0,
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

export async function seedDashboardSession(page, request) {
  const session = buildTestSession();
  const response = await request.post('http://127.0.0.1:8000/api/session/sync', {
    data: session,
    headers: authHeaders(),
  });
  expect(response.ok()).toBeTruthy();
  await prepareAuthenticatedPage(page, session);
  await page.waitForSelector('[data-testid="audit-header"]');
}
