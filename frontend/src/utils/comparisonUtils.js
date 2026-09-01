export function resultTypeLabel(type) {
  const map = {
    matched: 'Matched',
    missing_in_ewb: 'Missing in EWB',
    missing_in_gstr1: 'Missing in GSTR-1',
    value_mismatch: 'Value Mismatch',
    duplicate: 'Duplicate',
  };
  return map[type] || type || '—';
}
