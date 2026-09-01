import { authHeaders } from './client';

const API_BASE_URL = '';

export async function classifyEwayFiles(files, {
  dealerGstin = '',
  expectedDirection = null,
  gstr1Files = [],
  gstr2aFiles = [],
} = {}) {
  const formData = new FormData();
  files.forEach((file) => formData.append('ewb_files', file));
  gstr1Files.forEach((file) => formData.append('gstr1_files', file));
  gstr2aFiles.forEach((file) => formData.append('gstr2a_files', file));

  const params = new URLSearchParams();
  if (dealerGstin) params.set('dealer_gstin', dealerGstin);
  if (expectedDirection) params.set('expected_direction', expectedDirection);

  const response = await fetch(`${API_BASE_URL}/api/eway/classify?${params}`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Classification failed');
  }
  return data;
}

export async function validateEwayFiles(files, expectedDirection, dealerGstin = '') {
  const formData = new FormData();
  files.forEach((file) => formData.append('ewb_files', file));
  const params = new URLSearchParams({ expected_direction: expectedDirection });
  if (dealerGstin) params.set('dealer_gstin', dealerGstin);

  const response = await fetch(`${API_BASE_URL}/api/eway/validate?${params}`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Validation failed');
  }
  return data;
}

export async function mergeEwayWorkflow(files, direction, ignoreMissing = false, dealerGstin = '') {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const params = new URLSearchParams({ ignore_missing: String(ignoreMissing) });
  if (dealerGstin) params.set('dealer_gstin', dealerGstin);

  const response = await fetch(
    `${API_BASE_URL}/api/merge/eway/${direction}?${params}`,
    { method: 'POST', headers: authHeaders(), body: formData },
  );

  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.message || data.detail || 'E-Way merge failed');
    error.payload = data;
    throw error;
  }
  return data;
}
