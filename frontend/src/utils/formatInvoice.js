export function normalizeInvoice(value) {
  if (!value) return '';
  return String(value).trim().toUpperCase().replace(/[^A-Z0-9/-]/g, '');
}

export function formatInvoice(value) {
  const n = normalizeInvoice(value);
  return n || '—';
}
