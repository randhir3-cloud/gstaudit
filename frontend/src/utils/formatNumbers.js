export function formatCount(n) {
  if (n == null || Number.isNaN(n)) return '—';
  return Number(n).toLocaleString('en-IN');
}

export function formatPercent(n) {
  if (n == null || Number.isNaN(n)) return '0%';
  return `${Number(n).toFixed(2)}%`;
}

export function formatDate(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const day = String(d.getDate()).padStart(2, '0');
    const mon = d.toLocaleString('en-GB', { month: 'short' });
    return `${day}-${mon}-${d.getFullYear()}`;
  } catch {
    return iso;
  }
}

export function shortDatasetLabel(key, labels) {
  const map = {
    gstr1: 'GSTR-1',
    gstr2a: 'GSTR-2A',
    ewb_outward: 'EWB Out',
    ewb_inward: 'EWB In',
  };
  return map[key] || labels?.[key] || key;
}
