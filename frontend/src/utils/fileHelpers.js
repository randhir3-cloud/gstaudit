const MONTH_MAP = {
  '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
  '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
  '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
};

const MONTH_NAMES = {
  january: { short: 'Jan', num: 1 },
  jan: { short: 'Jan', num: 1 },
  february: { short: 'Feb', num: 2 },
  feb: { short: 'Feb', num: 2 },
  march: { short: 'Mar', num: 3 },
  mar: { short: 'Mar', num: 3 },
  april: { short: 'Apr', num: 4 },
  apr: { short: 'Apr', num: 4 },
  may: { short: 'May', num: 5 },
  june: { short: 'Jun', num: 6 },
  jun: { short: 'Jun', num: 6 },
  july: { short: 'Jul', num: 7 },
  jul: { short: 'Jul', num: 7 },
  august: { short: 'Aug', num: 8 },
  aug: { short: 'Aug', num: 8 },
  september: { short: 'Sep', num: 9 },
  sep: { short: 'Sep', num: 9 },
  sept: { short: 'Sep', num: 9 },
  october: { short: 'Oct', num: 10 },
  oct: { short: 'Oct', num: 10 },
  november: { short: 'Nov', num: 11 },
  nov: { short: 'Nov', num: 11 },
  december: { short: 'Dec', num: 12 },
  dec: { short: 'Dec', num: 12 },
};

export function extractPeriodFromFilename(name) {
  if (!name) return '—';
  // 1. Standard pattern: _MMYYYY_
  const match = name.match(/_(\d{2})(\d{4})_/);
  if (match) {
    return `${MONTH_MAP[match[1]] || match[1]}-${match[2]}`;
  }

  // 2. Look for Month Name + Optional Year in filename (e.g., "Inward April 1.xls", "Inward Jan 23 1.xls")
  const lower = name.toLowerCase();
  const yearMatch = lower.match(/\b(20\d{2}|\d{2})\b/);
  const yr = yearMatch ? (yearMatch[1].length === 2 ? `20${yearMatch[1]}` : yearMatch[1]) : '';

  for (const [mName, info] of Object.entries(MONTH_NAMES)) {
    const re = new RegExp(`\\b${mName}\\b`, 'i');
    if (re.test(lower)) {
      return yr ? `${info.short}-${yr}` : info.short;
    }
  }

  return '—';
}

export function getFYMonthSortKey(name) {
  if (!name) return 999999;
  const match = name.match(/_(\d{2})(\d{4})_/);
  if (match) {
    const mm = parseInt(match[1], 10);
    const yyyy = parseInt(match[2], 10);
    if (mm >= 4) return yyyy * 100 + (mm - 3);
    return (yyyy - 1) * 100 + (mm + 9);
  }

  const lower = name.toLowerCase();
  for (const [mName, info] of Object.entries(MONTH_NAMES)) {
    const re = new RegExp(`\\b${mName}\\b`, 'i');
    if (re.test(lower)) {
      const mm = info.num;
      const order = mm >= 4 ? mm - 3 : mm + 9;
      return 200000 + order;
    }
  }

  return 999999;
}

export function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function base64ToBlob(base64, mimeType) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: mimeType });
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
