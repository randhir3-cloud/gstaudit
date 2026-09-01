const GSTIN_RE = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/;

export function normalizeGSTIN(value) {
  if (!value) return '';
  return String(value).trim().toUpperCase().replace(/\s+/g, '');
}

export function formatGSTIN(value) {
  const n = normalizeGSTIN(value);
  if (!n) return '—';
  return n;
}

export function isValidGSTIN(value) {
  return GSTIN_RE.test(normalizeGSTIN(value));
}
