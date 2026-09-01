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

/** Convert a sheet to 2D array of rows with stringified IDs */
export function sheetTo2DArray(sheet, options = {}) {
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
