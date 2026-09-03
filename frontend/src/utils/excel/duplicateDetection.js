import * as XLSX from 'xlsx';
import { readWorkbookRaw, sheetTo2DArray, cleanStr, normalizeRate, normalizeNumeric } from './excelUtils.js';

export const META_SHEET_NAME = 'GST_AUDIT_META';
export const MERGER_VERSION = '1.0.0';

/**
 * Creates a standardized metadata sheet for GST Audit Merged workbooks.
 */
export function createMergeMetadataSheet(info = {}) {
  const rows = [
    ['Property', 'Value'],
    ['Generated_By', 'GST Audit Merger'],
    ['Merger_Version', MERGER_VERSION],
    ['Merge_Type', info.mergeType || 'UNKNOWN'],
    ['Generated_At', new Date().toISOString()],
    ['GSTIN', info.gstin || ''],
    ['Legal_Name', info.legalName || ''],
    ['Financial_Year', info.financialYear || ''],
    ['Source_File_Count', info.sourceFileCount || 0],
    ['Source_Files', Array.isArray(info.sourceFiles) ? info.sourceFiles.join(', ') : (info.sourceFiles || '')],
    ['Total_Merged_Rows', info.totalRows || 0],
  ];

  return XLSX.utils.aoa_to_sheet(rows);
}

/**
 * Detects whether a workbook is a previously merged GST Audit output.
 * Checks for explicit GST_AUDIT_META sheet, known output columns (Source_File, Source_Sheet, EWB_Direction),
 * and distinctive multi-file merged patterns.
 */
export function detectPreviouslyMergedWorkbook(wb, filename = '') {
  if (!wb || !wb.SheetNames) {
    return { isPreviouslyMerged: false, confidence: 0, reason: '' };
  }

  // 1. Explicit GST_AUDIT_META sheet detection (100% confidence)
  const metaSheetName = wb.SheetNames.find(
    (name) => name.trim().toUpperCase() === META_SHEET_NAME
  );
  if (metaSheetName) {
    const ws = wb.Sheets[metaSheetName];
    const rows = sheetTo2DArray(ws);
    let mergeType = '';
    let generatedBy = '';
    for (const r of rows) {
      const key = cleanStr(r[0]).toLowerCase();
      const val = cleanStr(r[1]);
      if (key === 'generated_by') generatedBy = val;
      if (key === 'merge_type') mergeType = val;
    }
    if (generatedBy.toLowerCase().includes('gst audit')) {
      return {
        isPreviouslyMerged: true,
        confidence: 1.0,
        mergeType: mergeType || 'unknown',
        reason: 'Explicit GST_AUDIT_META metadata marker found in workbook',
      };
    }
  }

  // 2. Structural marker detection in E-Way workbooks
  // E-Way merged output has sheets like "EWB_Inward" or "EWB_Outward" with columns:
  // "Source_Period", "Source_File", "Source_Sheet", "EWB_Direction"
  for (const name of wb.SheetNames) {
    const ws = wb.Sheets[name];
    const rows = sheetTo2DArray(ws);
    if (rows.length > 0) {
      const headers = (rows[0] || []).map((h) => cleanStr(h).toLowerCase());
      const hasEwbDir = headers.includes('ewb_direction');
      const hasSrcFile = headers.includes('source_file');
      const hasSrcSheet = headers.includes('source_sheet');
      const hasSrcPeriod = headers.includes('source_period');

      if ((hasEwbDir && hasSrcFile) || (hasSrcFile && hasSrcSheet && hasSrcPeriod)) {
        return {
          isPreviouslyMerged: true,
          confidence: 0.98,
          mergeType: name.toLowerCase().includes('inward') ? 'eway_inward' : 'eway_outward',
          reason: 'Structural E-Way merged output columns (Source_File, Source_Sheet, EWB_Direction) detected',
        };
      }
    }
  }

  // 3. Structural marker detection in GSTR-1 and GSTR-2A workbooks
  // GSTR merged files have "Source_Period" column appended to every table header
  let gstrHeaderWithSourcePeriod = 0;
  for (const name of wb.SheetNames) {
    const lowerName = name.trim().toLowerCase();
    if (lowerName === 'read me' || lowerName === 'readme') continue;

    const ws = wb.Sheets[name];
    const rows = sheetTo2DArray(ws);
    // Scan up to row 10 for header containing Source_Period
    for (let r = 0; r < Math.min(rows.length, 10); r++) {
      const headerRow = rows[r] || [];
      const headers = headerRow.map((h) => cleanStr(h).toLowerCase());
      if (headers.includes('source_period') || headers.includes('source period')) {
        gstrHeaderWithSourcePeriod++;
        break;
      }
    }
  }

  if (gstrHeaderWithSourcePeriod >= 2) {
    const isGstr1 = wb.SheetNames.some((n) => n.toLowerCase().includes('b2b') || n.toLowerCase().includes('cdnr'));
    return {
      isPreviouslyMerged: true,
      confidence: 0.95,
      mergeType: isGstr1 ? 'gstr1' : 'gstr2a',
      reason: 'Structural GSTR merged output columns (Source_Period) detected across multiple sheets',
    };
  }

  return { isPreviouslyMerged: false, confidence: 0, reason: '' };
}

/**
 * Computes a deterministic content fingerprint (SHA-256) of meaningful workbook contents.
 * Normalizes sheet names, non-empty data rows, and cell values.
 */
export async function computeWorkbookFingerprint(file, wb = null) {
  const workbook = wb || (await readWorkbookRaw(file));
  const normalizedParts = [];

  for (const sheetName of workbook.SheetNames) {
    const lowerName = sheetName.trim().toLowerCase();
    if (lowerName === 'read me' || lowerName === 'readme' || lowerName === META_SHEET_NAME.toLowerCase()) {
      continue;
    }

    normalizedParts.push(`SHEET:${lowerName}`);
    const rows = sheetTo2DArray(workbook.Sheets[sheetName]);

    for (const row of rows) {
      if (!row || !row.some((c) => cleanStr(c) !== '')) continue;
      const cleanRowStr = row
        .map((c) => (c == null ? '' : String(c).trim().toLowerCase()))
        .join('|');
      normalizedParts.push(cleanRowStr);
    }
  }

  const textToHash = normalizedParts.join('\n');
  if (!textToHash) {
    // If no sheets have data, fallback to filename + size
    return `${file.name}_${file.size}`;
  }

  try {
    const encoder = new TextEncoder();
    const data = encoder.encode(textToHash);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  } catch {
    // Fallback simple hash if Web Crypto unavailable
    let hash = 0;
    for (let i = 0; i < textToHash.length; i++) {
      hash = (hash << 5) - hash + textToHash.charCodeAt(i);
      hash |= 0;
    }
    return `hash_${hash}`;
  }
}

/**
 * Normalizes a string for record key comparison
 */
function normKeyVal(val) {
  if (val == null) return '';
  return String(val).trim().toUpperCase().replace(/\s+/g, ' ');
}

/**
 * Builds a composite unique record key for an E-Way Bill row.
 * E-Way Bills are identified by EWB Number + Document Number + Doc Date + Item/Taxable Value.
 * This guarantees distinguishing multi-item invoices while eliminating duplicate full transactions across files.
 */
export function buildEwayRecordKey(row, headers = []) {
  if (!row || row.length === 0) return '';

  // 1. Try to find EWB No, Doc No, Doc Dt, and Taxable Value by header index if headers provided
  if (headers.length > 0) {
    const ewbIdx = headers.findIndex((h) => /^ewb no/i.test(cleanStr(h)));
    const fromIdx = headers.findIndex((h) => /from gstin/i.test(cleanStr(h)));
    const toIdx = headers.findIndex((h) => /to gstin/i.test(cleanStr(h)));
    const docIdx = headers.findIndex((h) => /doc no/i.test(cleanStr(h)));
    const assessValIdx = headers.findIndex((h) => /assess val/i.test(cleanStr(h)));
    const taxValIdx = headers.findIndex((h) => /tax val/i.test(cleanStr(h)));
    const hsnIdx = headers.findIndex((h) => /hsn/i.test(cleanStr(h)));
    const vehicleIdx = headers.findIndex((h) => /vehicle/i.test(cleanStr(h)));

    const ewbVal = ewbIdx !== -1 ? normKeyVal(row[ewbIdx]) : '';
    const fromVal = fromIdx !== -1 ? normKeyVal(row[fromIdx]) : '';
    const toVal = toIdx !== -1 ? normKeyVal(row[toIdx]) : '';
    const docVal = docIdx !== -1 ? normKeyVal(row[docIdx]) : '';
    const assessVal = assessValIdx !== -1 ? normKeyVal(row[assessValIdx]) : '';
    const taxVal = taxValIdx !== -1 ? normKeyVal(row[taxValIdx]) : '';
    const hsnVal = hsnIdx !== -1 ? normKeyVal(row[hsnIdx]) : '';
    const vehicleVal = vehicleIdx !== -1 ? normKeyVal(row[vehicleIdx]) : '';

    if (ewbVal && ewbVal !== '—') {
      return `EWB_${ewbVal}_${docVal}_${assessVal}_${taxVal}_${hsnVal}_${vehicleVal}`;
    }
    if (fromVal && toVal && docVal) {
      return `DOC_${fromVal}_${toVal}_${docVal}_${assessVal}_${taxVal}_${hsnVal}_${vehicleVal}`;
    }
  }

  // Fallback: full normalized non-metadata row string
  const cleanCells = row.slice(0, Math.max(row.length - 4, 1)).map(normKeyVal);
  return `ROW_${cleanCells.join('_')}`;
}

/**
 * Builds a composite unique record key for a GSTR-1 row based on sheet type and column values.
 */
export function buildGstr1RecordKey(sheetName, row, headers = [], period = '') {
  if (!row || row.length === 0) return '';
  const sheet = sheetName.trim().toLowerCase();

  // Find column indices
  const gstinIdx = headers.findIndex((h) => /gstin|uin/i.test(cleanStr(h)));
  const invIdx = headers.findIndex((h) => /invoice number|inv no|invoice no/i.test(cleanStr(h)) && !/original/i.test(cleanStr(h)));
  const dateIdx = headers.findIndex((h) => /date|dt/i.test(cleanStr(h)) && !/original/i.test(cleanStr(h)));
  const noteIdx = headers.findIndex((h) => /note number|note no/i.test(cleanStr(h)) && !/original/i.test(cleanStr(h)));
  const rateIdx = headers.findIndex((h) => /^rate$|^rate\s*\(/i.test(cleanStr(h)));
  const valIdx = headers.findIndex((h) => /taxable value|taxable val/i.test(cleanStr(h)));
  const posIdx = headers.findIndex((h) => /place of supply/i.test(cleanStr(h)));
  const igstIdx = headers.findIndex((h) => /integrated tax|igst/i.test(cleanStr(h)));
  const cgstIdx = headers.findIndex((h) => /central tax|cgst/i.test(cleanStr(h)));
  const sgstIdx = headers.findIndex((h) => /state.*tax|sgst|ut tax/i.test(cleanStr(h)));
  const cessIdx = headers.findIndex((h) => /cess/i.test(cleanStr(h)));
  const hsnIdx = headers.findIndex((h) => /^hsn/i.test(cleanStr(h)));
  const uqcIdx = headers.findIndex((h) => /uqc/i.test(cleanStr(h)));
  const descIdx = headers.findIndex((h) => /description/i.test(cleanStr(h)));
  const docNatureIdx = headers.findIndex((h) => /nature of document/i.test(cleanStr(h)));
  const srFromIdx = headers.findIndex((h) => /sr\.?\s*no\.?\s*from/i.test(cleanStr(h)));
  const srToIdx = headers.findIndex((h) => /sr\.?\s*no\.?\s*to/i.test(cleanStr(h)));

  const gstin = gstinIdx !== -1 ? normKeyVal(row[gstinIdx]) : '';
  const inv = invIdx !== -1 ? normKeyVal(row[invIdx]) : '';
  const dt = dateIdx !== -1 ? normKeyVal(row[dateIdx]) : '';
  const note = noteIdx !== -1 ? normKeyVal(row[noteIdx]) : '';
  const pos = posIdx !== -1 ? normKeyVal(row[posIdx]) : '';
  const rateVal = rateIdx !== -1 ? normalizeRate(row[rateIdx]) : null;
  const rateStr = rateVal === null ? 'NORATE' : `RATE_${rateVal}`;
  const taxVal = valIdx !== -1 ? normalizeNumeric(row[valIdx]).toFixed(2) : '';
  const igstVal = igstIdx !== -1 ? normalizeNumeric(row[igstIdx]).toFixed(2) : '';
  const cgstVal = cgstIdx !== -1 ? normalizeNumeric(row[cgstIdx]).toFixed(2) : '';
  const sgstVal = sgstIdx !== -1 ? normalizeNumeric(row[sgstIdx]).toFixed(2) : '';
  const cessVal = cessIdx !== -1 ? normalizeNumeric(row[cessIdx]).toFixed(2) : '';
  const hsn = hsnIdx !== -1 ? normKeyVal(row[hsnIdx]) : '';
  const uqc = uqcIdx !== -1 ? normKeyVal(row[uqcIdx]) : '';
  const desc = descIdx !== -1 ? normKeyVal(row[descIdx]) : '';
  const docNature = docNatureIdx !== -1 ? normKeyVal(row[docNatureIdx]) : '';
  const srFrom = srFromIdx !== -1 ? normKeyVal(row[srFromIdx]) : '';
  const srTo = srToIdx !== -1 ? normKeyVal(row[srToIdx]) : '';
  const srcPeriod = normKeyVal(period);

  if (sheet.includes('b2b') || sheet.includes('b2cl') || sheet.includes('exp')) {
    if (inv) return `b2b_${srcPeriod}_${gstin}_${inv}_${dt}_${pos}_${rateStr}_${taxVal}_${igstVal}_${cgstVal}_${sgstVal}_${cessVal}`;
  }
  if (sheet.includes('cdnr') || sheet.includes('cdnur')) {
    if (note) return `${sheet}_${srcPeriod}_${gstin}_${note}_${dt}_${pos}_${rateStr}_${taxVal}_${igstVal}_${cgstVal}_${sgstVal}_${cessVal}`;
  }
  if (sheet.includes('b2cs')) {
    return `b2cs_${srcPeriod}_${pos}_${rateStr}_${taxVal}_${igstVal}_${cgstVal}_${sgstVal}_${cessVal}`;
  }
  if (sheet.includes('hsn')) {
    if (hsn) return `hsn_${srcPeriod}_${hsn}_${desc}_${uqc}_${rateStr}_${taxVal}_${igstVal}_${cgstVal}_${sgstVal}_${cessVal}`;
  }
  if (sheet.includes('docs')) {
    return `docs_${srcPeriod}_${docNature}_${srFrom}_${srTo}`;
  }

  // Full row fallback (excluding Source_Period at end if present)
  const cleanCells = row.slice(0, Math.max(row.length - 1, 1)).map(normKeyVal);
  return `${sheet}_${srcPeriod}_${cleanCells.join('_')}`;
}

/**
 * Builds a composite unique record key for a GSTR-2A row.
 */
export function buildGstr2aRecordKey(sheetName, row, headers = [], period = '') {
  if (!row || row.length === 0) return '';
  const sheet = sheetName.trim().toLowerCase();

  const gstinIdx = headers.findIndex((h) => /gstin/i.test(cleanStr(h)));
  const invIdx = headers.findIndex((h) => /invoice number|document number/i.test(cleanStr(h)) && !/original/i.test(cleanStr(h)));
  const noteIdx = headers.findIndex((h) => /note number/i.test(cleanStr(h)) && !/original/i.test(cleanStr(h)));
  const dtIdx = headers.findIndex((h) => /date/i.test(cleanStr(h)) && !/original/i.test(cleanStr(h)));
  const posIdx = headers.findIndex((h) => /place of supply/i.test(cleanStr(h)));
  const rateIdx = headers.findIndex((h) => /^rate/i.test(cleanStr(h)));
  const valIdx = headers.findIndex((h) => /taxable value/i.test(cleanStr(h)));
  const igstIdx = headers.findIndex((h) => /integrated tax|igst/i.test(cleanStr(h)));
  const cgstIdx = headers.findIndex((h) => /central tax|cgst/i.test(cleanStr(h)));
  const sgstIdx = headers.findIndex((h) => /state.*tax|sgst|ut tax/i.test(cleanStr(h)));
  const cessIdx = headers.findIndex((h) => /cess/i.test(cleanStr(h)));

  const gstin = gstinIdx !== -1 ? normKeyVal(row[gstinIdx]) : '';
  const inv = invIdx !== -1 ? normKeyVal(row[invIdx]) : '';
  const note = noteIdx !== -1 ? normKeyVal(row[noteIdx]) : '';
  const dt = dtIdx !== -1 ? normKeyVal(row[dtIdx]) : '';
  const pos = posIdx !== -1 ? normKeyVal(row[posIdx]) : '';
  const rateVal = rateIdx !== -1 ? normalizeRate(row[rateIdx]) : null;
  const rateStr = rateVal === null ? 'NORATE' : `RATE_${rateVal}`;
  const taxVal = valIdx !== -1 ? normalizeNumeric(row[valIdx]).toFixed(2) : '';
  const igstVal = igstIdx !== -1 ? normalizeNumeric(row[igstIdx]).toFixed(2) : '';
  const cgstVal = cgstIdx !== -1 ? normalizeNumeric(row[cgstIdx]).toFixed(2) : '';
  const sgstVal = sgstIdx !== -1 ? normalizeNumeric(row[sgstIdx]).toFixed(2) : '';
  const cessVal = cessIdx !== -1 ? normalizeNumeric(row[cessIdx]).toFixed(2) : '';
  const srcPeriod = normKeyVal(period);

  const docNo = inv || note;
  if (docNo) {
    return `${sheet}_${srcPeriod}_${gstin}_${docNo}_${dt}_${pos}_${rateStr}_${taxVal}_${igstVal}_${cgstVal}_${sgstVal}_${cessVal}`;
  }

  const cleanCells = row.slice(0, Math.max(row.length - 1, 1)).map(normKeyVal);
  return `${sheet}_${srcPeriod}_${cleanCells.join('_')}`;
}
