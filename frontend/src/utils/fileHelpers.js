const MONTH_MAP = {
  '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
  '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
  '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
};

export function extractPeriodFromFilename(name) {
  const match = name.match(/_(\d{2})(\d{4})_/);
  if (match) {
    return `${MONTH_MAP[match[1]] || match[1]}-${match[2]}`;
  }
  return 'Unknown Period';
}

export function getFYMonthSortKey(name) {
  const match = name.match(/_(\d{2})(\d{4})_/);
  if (match) {
    const mm = parseInt(match[1], 10);
    const yyyy = parseInt(match[2], 10);
    if (mm >= 4) return yyyy * 100 + (mm - 3);
    return (yyyy - 1) * 100 + (mm + 9);
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
