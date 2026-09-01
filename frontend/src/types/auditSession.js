export const DATASET_KEYS = ['gstr1', 'gstr2a', 'ewb_outward', 'ewb_inward'];

export const DATASET_LABELS = {
  gstr1: 'GSTR-1',
  gstr2a: 'GSTR-2A',
  ewb_outward: 'EWB OUTWARD',
  ewb_inward: 'EWB INWARD',
};

export const EMPTY_DATASET = {
  dataset_key: '',
  label: '',
  source_files: [],
  staged_files: [],
  merged: false,
  workbook_id: '',
  current_dataset: '',
  dealer_gstin: '',
  financial_year: '',
  row_count: 0,
  invoice_count: 0,
  uploaded_months: [],
  missing_months: [],
  duplicate_months: [],
  last_upload_at: '',
  last_merge_at: '',
  merge_processing_ms: 0,
  status: 'empty',
  preview_available: false,
  download_available: false,
};

export function buildEmptyDatasets() {
  return Object.fromEntries(
    DATASET_KEYS.map((key) => [
      key,
      { ...EMPTY_DATASET, dataset_key: key, label: DATASET_LABELS[key] },
    ]),
  );
}

export function buildSessionId(gstin, financialYear) {
  const raw = `${(gstin || '').toUpperCase()}:${(financialYear || '').trim()}`;
  let hash = 0;
  for (let i = 0; i < raw.length; i += 1) {
    hash = (hash * 31 + raw.charCodeAt(i)) >>> 0;
  }
  return `session_${hash.toString(16).padStart(12, '0')}`;
}

export const STORAGE_KEY = 'gst_audit_session';
