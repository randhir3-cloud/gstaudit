import { extractDealerMetadataFromFiles } from '../utils/excel/dealerMetadataService';

export async function extractDealerMetadata(files, returnType) {
  return extractDealerMetadataFromFiles(files, returnType);
}

export function parseWorkbookMetadataHeader(response) {
  if (!response?.headers?.get) return null;
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
