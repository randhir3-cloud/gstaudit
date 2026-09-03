import * as XLSX from 'xlsx';

export const MONTH_MAP = {
  '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
  '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
  '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
};

export const FULL_MONTH_MAP = {
  '01': 'January', '02': 'February', '03': 'March', '04': 'April',
  '05': 'May', '06': 'June', '07': 'July', '08': 'August',
  '09': 'September', '10': 'October', '11': 'November', '12': 'December',
};

export const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;

export function fySortKey(mm, yyyy) {
  const mmInt = parseInt(mm, 10);
  const yyyyInt = parseInt(yyyy, 10);
  if (mmInt >= 4) {
    return yyyyInt * 100 + (mmInt - 3);
  }
  return (yyyyInt - 1) * 100 + (mmInt + 9);
}

export function fyKeyToLabel(key) {
  const idx = key % 100;
  const fyStartYr = Math.floor(key / 100);
  let calMonth;
  let calYear;
  if (idx <= 9) {
    calMonth = idx + 3;
    calYear = fyStartYr;
  } else {
    calMonth = idx - 9;
    calYear = fyStartYr + 1;
  }
  const mmStr = String(calMonth).padStart(2, '0');
  return `${FULL_MONTH_MAP[mmStr] || calMonth} ${calYear}`;
}

export function nextFyKey(key) {
  const idx = key % 100;
  const fyYear = Math.floor(key / 100);
  if (idx < 12) {
    return fyYear * 100 + (idx + 1);
  }
  return (fyYear + 1) * 100 + 1;
}

export function fileFyKey(filename) {
  const m = filename.match(/_(\d{2})(\d{4})_/);
  if (m) {
    return fySortKey(m[1], m[2]);
  }
  return 999999;
}

export function extractPeriod(filename) {
  const m = filename.match(/_(\d{2})(\d{4})_/);
  if (m) {
    const mm = m[1];
    const yyyy = m[2];
    return `${MONTH_MAP[mm] || mm}-${yyyy}`;
  }
  const parts = filename.split('.');
  return parts[0] || filename;
}

export function findMissingMonths(filenames) {
  const present = new Set();
  for (const fname of filenames) {
    const m = fname.match(/_(\d{2})(\d{4})_/);
    if (m) {
      present.add(fySortKey(m[1], m[2]));
    }
  }

  if (present.size < 2) return [];

  const sortedPresent = Array.from(present).sort((a, b) => a - b);
  const minKey = sortedPresent[0];
  const maxKey = sortedPresent[sortedPresent.length - 1];
  const missing = [];
  let cur = nextFyKey(minKey);
  while (cur < maxKey) {
    if (!present.has(cur)) {
      missing.push(fyKeyToLabel(cur));
    }
    cur = nextFyKey(cur);
  }
  return missing;
}

/** Read a file object into an ArrayBuffer or binary string */
export async function readFileAsArrayBuffer(file) {
  if (typeof file.arrayBuffer === 'function') {
    return file.arrayBuffer();
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(new Error('Failed to read file: ' + file.name));
    reader.readAsArrayBuffer(file);
  });
}

/** Read workbook from file */
export async function readWorkbook(file) {
  const buffer = await readFileAsArrayBuffer(file);
  return XLSX.read(buffer, { type: 'array', cellDates: true, cellStyles: true, raw: false });
}

/** Read raw workbook (keeps string formats where possible) */
export async function readWorkbookRaw(file) {
  const buffer = await readFileAsArrayBuffer(file);
  return XLSX.read(buffer, { type: 'array', cellDates: true, raw: true });
}

/** Recalculates !ref range from actual cell keys in case portal file has truncated metadata */
export function updateSheetRefRange(sheet) {
  if (!sheet) return;
  const keys = Object.keys(sheet).filter((k) => !k.startsWith('!'));
  if (keys.length === 0) return;
  let minR = Infinity;
  let maxR = -Infinity;
  let minC = Infinity;
  let maxC = -Infinity;
  for (const k of keys) {
    const cell = XLSX.utils.decode_cell(k);
    if (cell.r < minR) minR = cell.r;
    if (cell.r > maxR) maxR = cell.r;
    if (cell.c < minC) minC = cell.c;
    if (cell.c > maxC) maxC = cell.c;
  }
  if (minR !== Infinity && maxR >= 0) {
    sheet['!ref'] = XLSX.utils.encode_range({
      s: { r: minR, c: minC },
      e: { r: maxR, c: maxC },
    });
  }
}

/** Convert a sheet to 2D array of rows with stringified IDs */
export function sheetTo2DArray(sheet, options = {}) {
  if (!sheet) return [];
  updateSheetRefRange(sheet);
  return XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    defval: '',
    raw: false,
    dateNF: 'dd/mm/yyyy',
    ...options,
  });
}

/** Convert workbook to blob */
export function workbookToBlob(wb) {
  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
  return new Blob([wbout], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
}

/** Clean string value */
export function cleanStr(val) {
  if (val == null) return '';
  return String(val).trim();
}

/**
 * Normalizes GST Rate values for comparison and grouping.
 * Returns canonical numeric float or null for non-applicable / missing rates.
 * Crucially distinguishes 0 (0% GST rate) from null (missing/'-'/NA).
 */
export function normalizeRate(val) {
  if (val == null) return null;
  const s = cleanStr(val);
  if (!s || s === '-' || s === '—' || s.toLowerCase() === 'na' || s.toLowerCase() === 'n/a') {
    return null;
  }
  const cleanNum = s.replace(/%/g, '').trim();
  const num = parseFloat(cleanNum);
  if (isNaN(num)) return null;
  return Number(num.toFixed(4));
}

/**
 * Formats a normalized rate for clean user-facing Excel output.
 */
export function formatCleanRate(val) {
  const norm = normalizeRate(val);
  if (norm === null) return '-';
  return norm;
}

/**
 * Safely parses any cell value into a numeric float.
 * Handles strings with commas, currency symbols, and empty / '-' values.
 */
export function normalizeNumeric(val) {
  if (val == null) return 0.0;
  if (typeof val === 'number') {
    return isNaN(val) ? 0.0 : val;
  }
  const s = cleanStr(val).replace(/,/g, '').replace(/[₹$]/g, '').trim();
  if (!s || s === '-' || s === '—') return 0.0;
  const num = parseFloat(s);
  return isNaN(num) ? 0.0 : num;
}

/**
 * Structural detection of portal-generated Total / Subtotal rows.
 * Uses structural data signals (-Total suffix, Total labels) rather than relying solely on formatting.
 */
export function isPortalTotalRow(row, numColIdx = -1) {
  if (!row || !Array.isArray(row)) return false;

  // 1. Check designated document number column if known
  if (numColIdx >= 0 && numColIdx < row.length) {
    const val = cleanStr(row[numColIdx]);
    if (/-(?:total|subtotal)$/i.test(val)) return true;
    if (/^(?:total|grand total|subtotal)$/i.test(val)) return true;
  }

  // 2. Scan all cells for '-Total' suffix or explicit Total keyword in identity columns
  for (let c = 0; c < row.length; c++) {
    const s = cleanStr(row[c]);
    if (!s) continue;
    if (/-(?:total|subtotal)$/i.test(s)) return true;
    if (c <= 5 && /^(?:total|grand total|subtotal)$/i.test(s)) return true;
  }

  return false;
}
