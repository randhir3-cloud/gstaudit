import * as XLSX from 'xlsx';
import {
  readWorkbook,
  sheetTo2DArray,
  workbookToBlob,
  fileFyKey,
  extractPeriod,
  findMissingMonths,
  FULL_MONTH_MAP,
  cleanStr,
  GSTIN_REGEX,
} from './excelUtils';
import { extractDealerMetadataFromFiles } from './dealerMetadataService';

const GSTR2A_SKIP_SHEETS = new Set(['read me', 'readme']);
const GSTR2A_NUMBER_HEADERS = new Set([
  'invoice number', 'note number', 'isd invoice number', 'number',
  'document number', 'document number ', 'note number ',
]);

const GSTR2A_HEADER_HINTS = [
  'gstin', 'invoice number', 'document number', 'note number',
  'original details', 'revised details', 'trade/legal', 'place of supply',
  'taxable value', 'document type', 'invoice type', 'note type',
  'eligibility of itc', 'isd document', 'document details',
];

const DATE_REGEX = /^\d{2}-\d{2}-\d{4}$/;

function normalizeHeaderKey(label) {
  return cleanStr(label).toLowerCase();
}

function isNumberHeaderLabel(label) {
  const key = normalizeHeaderKey(label);
  if (!key || key.length > 40) return false;
  if (GSTR2A_NUMBER_HEADERS.has(key)) return true;
  return key.endsWith('number');
}

function isGstr2aDataRow(row) {
  if (!row || !row.some((val) => cleanStr(val) !== '')) return false;

  const rowText = row.map((c) => normalizeHeaderKey(c)).join(' ');

  if (GSTR2A_HEADER_HINTS.some((hint) => rowText.includes(hint))) {
    const hasGstinOrTotal = row.some((c) => {
      const s = cleanStr(c);
      return GSTIN_REGEX.test(s) || s.endsWith('-Total');
    });
    if (!hasGstinOrTotal) return false;
  }

  for (let c = 0; c < row.length; c++) {
    const val = row[c];
    if (val == null) continue;
    const text = cleanStr(val);
    if (!text) continue;
    if (GSTIN_REGEX.test(text)) return true;
    if (text.endsWith('-Total')) return true;
    if (DATE_REGEX.test(text)) return true;
    if (typeof val === 'number' && c >= 5) return true;
  }

  return false;
}

function findGstr2aHeaderEnd(rows) {
  let lastHeader = 3; // default row index (0-based)
  const maxScan = Math.min(rows.length, 12);
  for (let r = 4; r < maxScan; r++) {
    const row = rows[r] || [];
    if (!row.some((v) => cleanStr(v) !== '')) continue;
    if (isGstr2aDataRow(row)) {
      break;
    }
    lastHeader = r;
  }
  return lastHeader;
}

function findGstr2aNumberColumn(rows, headerEnd) {
  const candidates = [];
  for (let r = 0; r <= headerEnd; r++) {
    const row = rows[r] || [];
    for (let c = 0; c < row.length; c++) {
      const label = cleanStr(row[c]);
      if (isNumberHeaderLabel(label)) {
        candidates.push({ r, c, label });
      }
    }
  }
  if (candidates.length === 0) return { r: 0, c: 0, label: '' };
  // Latest header row wins
  return candidates.reduce((prev, curr) => (curr.r >= prev.r && curr.c >= prev.c ? curr : prev), candidates[0]);
}

function extractGstr2aSummaryRows(rows, period, headerEnd, dataStart, numCol) {
  if (dataStart >= rows.length) return [];

  const summaryRows = [];
  const useSummaryFilter = numCol >= 0;

  let hasTotalSuffix = false;
  if (useSummaryFilter) {
    for (let r = dataStart; r < rows.length; r++) {
      const val = cleanStr(rows[r]?.[numCol]);
      if (val.endsWith('-Total')) {
        hasTotalSuffix = true;
        break;
      }
    }
  }

  for (let r = dataStart; r < rows.length; r++) {
    const row = rows[r];
    if (!row || !row.some((v) => cleanStr(v) !== '')) continue;
    if (!isGstr2aDataRow(row)) continue;

    if (useSummaryFilter) {
      const numVal = cleanStr(row[numCol]);
      if (hasTotalSuffix) {
        if (numVal.endsWith('-Total')) {
          summaryRows.push({ period, row });
        }
      } else {
        // Fallback: if not suffix, keep row
        summaryRows.push({ period, row });
      }
    } else {
      summaryRows.push({ period, row });
    }
  }

  return summaryRows;
}

export async function mergeGstr2aFiles(files, options = {}) {
  if (!files || files.length === 0) {
    throw new Error('No files provided for merging.');
  }

  // 1. Dealer consistency & metadata
  const meta = await extractDealerMetadataFromFiles(files, 'gstr2a');
  const dealer = meta.dealer;

  // 2. Missing months check
  const filenames = files.map((f) => f.name);
  const missingMonths = findMissingMonths(filenames);
  if (missingMonths.length > 0 && !options.ignoreMissing) {
    const err = new Error(`Missing months detected: ${missingMonths.join(', ')}`);
    err.payload = {
      error_type: 'missing_months',
      missing: missingMonths,
    };
    throw err;
  }

  // 3. Sort files by FY month
  const sortedFiles = [...files].sort((a, b) => fileFyKey(a.name) - fileFyKey(b.name));

  // Determine Tax Period Range
  const periodKeys = [];
  for (const file of sortedFiles) {
    const m = file.name.match(/_(\d{2})(\d{4})_/);
    if (m) {
      const mm = m[1];
      const yyyy = m[2];
      periodKeys.push({
        sortKey: parseInt(yyyy, 10) * 100 + parseInt(mm, 10),
        monthLabel: FULL_MONTH_MAP[mm] || mm,
        year: yyyy,
      });
    }
  }

  let taxPeriodText = 'Full Period';
  if (periodKeys.length > 0) {
    periodKeys.sort((a, b) => a.sortKey - b.sortKey);
    const first = periodKeys[0];
    const last = periodKeys[periodKeys.length - 1];
    const firstLabel = `${first.monthLabel} ${first.year}`;
    const lastLabel = `${last.monthLabel} ${last.year}`;
    taxPeriodText = firstLabel === lastLabel ? firstLabel : `${firstLabel} to ${lastLabel}`;
  }

  // 4. Load first file as template
  const templateWb = await readWorkbook(sortedFiles[0]);

  // 5. Collect summary data rows per sheet
  const sheetSummaryData = {}; // sheetName -> { period, row }[]

  for (const file of sortedFiles) {
    const period = extractPeriod(file.name);
    const wb = await readWorkbook(file);

    for (const sheetName of wb.SheetNames) {
      if (GSTR2A_SKIP_SHEETS.has(sheetName.trim().toLowerCase())) continue;

      const ws = wb.Sheets[sheetName];
      const rows = sheetTo2DArray(ws);
      if (rows.length === 0) continue;

      const headerEnd = findGstr2aHeaderEnd(rows);
      const { c: numCol } = findGstr2aNumberColumn(rows, headerEnd);
      const dataStart = headerEnd + 1;

      const summaries = extractGstr2aSummaryRows(rows, period, headerEnd, dataStart, numCol);

      if (!sheetSummaryData[sheetName]) {
        sheetSummaryData[sheetName] = [];
      }
      sheetSummaryData[sheetName].push(...summaries);
    }
  }

  // 6. Build final workbook
  const outWb = XLSX.utils.book_new();

  for (const sheetName of templateWb.SheetNames) {
    const lowerName = sheetName.trim().toLowerCase();

    if (GSTR2A_SKIP_SHEETS.has(lowerName)) {
      const srcSheet = templateWb.Sheets[sheetName];
      const readmeRows = sheetTo2DArray(srcSheet);
      // Row 2, Col E (idx [1][4]) is Tax Period in GSTR-2A
      if (readmeRows[1] && readmeRows[1][4] !== undefined) {
        readmeRows[1][4] = taxPeriodText;
      }
      const patchedSheet = XLSX.utils.aoa_to_sheet(readmeRows);
      XLSX.utils.book_append_sheet(outWb, patchedSheet, sheetName);
      continue;
    }

    const templateSheet = templateWb.Sheets[sheetName];
    const templateRows = sheetTo2DArray(templateSheet);
    const headerEnd = findGstr2aHeaderEnd(templateRows);

    // Keep all header rows from template
    const headerBlock = templateRows.slice(0, headerEnd + 1);

    // Add Source_Period to the last header row if not present
    const lastHdr = [...(headerBlock[headerEnd] || [])];
    lastHdr.push('Source_Period');
    headerBlock[headerEnd] = lastHdr;

    const dataRows = (sheetSummaryData[sheetName] || []).map(({ period, row }) => {
      return [...row, period];
    });

    const finalSheetRows = [...headerBlock, ...dataRows];
    const newWs = XLSX.utils.aoa_to_sheet(finalSheetRows);
    XLSX.utils.book_append_sheet(outWb, newWs, sheetName);
  }

  // Output filename
  let autoName = 'GSTR2A_Merged.xlsx';
  if (dealer.gstin && dealer.financial_year) {
    const safeGstin = dealer.gstin.replace(/[\\/:*?"<>|]/g, '_');
    const safeFy = dealer.financial_year.replace(/[\\/:*?"<>|]/g, '_');
    autoName = `GSTR2A_${safeGstin}_${safeFy}_Merged.xlsx`;
  }

  const blob = workbookToBlob(outWb);

  return {
    blob,
    suggested_filename: autoName,
    missing_months: missingMonths,
    dealer,
    workbook_id: meta.workbook_id,
    return_type: 'gstr2a',
    source_files: filenames,
    sheet_list: outWb.SheetNames,
  };
}
