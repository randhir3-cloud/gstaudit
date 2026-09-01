import { authHeaders } from './client';

const API_BASE_URL = '';

export async function extractDealerMetadata(files, returnType) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const response = await fetch(
    `${API_BASE_URL}/api/dealer/extract?return_type=${returnType}`,
    { method: 'POST', headers: authHeaders(), body: formData },
  );

  const data = await response.json();
  if (!response.ok) {
    const message = data.message || data.detail || 'Failed to extract dealer metadata';
    const error = new Error(message);
    error.payload = data;
    throw error;
  }
  return data;
}

export function parseWorkbookMetadataHeader(response) {
  const raw = response.headers.get('X-Workbook-Metadata');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function formatDealerMismatchError(payload) {
  if (!payload?.mismatches?.length) return payload?.message || 'Dealer validation failed';
  return payload.mismatches
    .map((m) => `${m.field} mismatch in ${m.source_file}: expected "${m.expected}", found "${m.found}"`)
    .join('; ');
}
