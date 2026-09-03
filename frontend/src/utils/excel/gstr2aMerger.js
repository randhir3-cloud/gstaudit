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
  normalizeRate,
  formatCleanRate,
  normalizeNumeric,
  isPortalTotalRow,
} from './excelUtils.js';
import { extractDealerMetadataFromFiles } from './dealerMetadataService.js';
import {
  buildGstr2aRecordKey,
  createMergeMetadataSheet,
  META_SHEET_NAME,
} from './duplicateDetection.js';

const GSTR2A_SKIP_SHEETS = new Set(['read me', 'readme', 'gst_audit_meta']);

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

/**
 * Identify if a row is a non-empty data candidate
 */
export function isGstr2aDataRow(row) {
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
    if (DATE_REGEX.test(text) || /^\d{2}\/\d{2}\/\d{4}$/.test(text)) return true;
    if (
      (typeof val === 'number' ||
        (!isNaN(parseFloat(text)) && isFinite(Number(text.replace(/,/g, ''))))) &&
      c >= 5
    ) {
      return true;
    }
  }

  return false;
}

/**
 * Detect the last header row for the sheet (typically row 6 or 7, 0-based idx 4 or 5)
 */
export function findGstr2aHeaderEnd(rows) {
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

/**
 * Builds a column name/alias index map from the header block
 */
function buildColumnIndexMap(headerBlock) {
  const colMap = {
    gstin: -1,
    tradeName: -1,
    invNumber: -1,
    invType: -1,
    invDate: -1,
    invValue: -1,
    pos: -1,
    reverseCharge: -1,
    rate: -1,
    taxableValue: -1,
    igst: -1,
    cgst: -1,
    sgst: -1,
    cess: -1,
    noteType: -1,
    noteNumber: -1,
    noteDate: -1,
    origInvNumber: -1,
    origInvDate: -1,
    origNoteNumber: -1,
    origNoteDate: -1,
    revInvNumber: -1,
    revInvDate: -1,
    revNoteNumber: -1,
    revNoteDate: -1,
  };

  const numCols = Math.max(...headerBlock.map((r) => (r ? r.length : 0)), 0);

  for (let c = 0; c < numCols; c++) {
    const cellTexts = headerBlock
      .map((r) => (r && r[c] != null ? cleanStr(r[c]).toLowerCase() : ''))
      .filter(Boolean);
    const joined = cellTexts.join(' ');

    if (/gstin/i.test(joined)) {
      if (colMap.gstin === -1) colMap.gstin = c;
    }
    if (/trade|legal name/i.test(joined)) {
      if (colMap.tradeName === -1) colMap.tradeName = c;
    }
    if (/invoice number|inv no/i.test(joined) && !/original/i.test(joined)) {
      if (colMap.invNumber === -1 || /details/i.test(joined)) colMap.invNumber = c;
    }
    if (/invoice type/i.test(joined)) {
      if (colMap.invType === -1) colMap.invType = c;
    }
    if (/invoice date/i.test(joined) && !/original/i.test(joined)) {
      if (colMap.invDate === -1) colMap.invDate = c;
    }
    if (/invoice value/i.test(joined) || /note value/i.test(joined) || /document value/i.test(joined)) {
      if (colMap.invValue === -1) colMap.invValue = c;
    }
    if (/place of supply/i.test(joined)) {
      if (colMap.pos === -1) colMap.pos = c;
    }
    if (/reverse charge/i.test(joined)) {
      if (colMap.reverseCharge === -1) colMap.reverseCharge = c;
    }
    if (/^rate|^rate\s*\(|gst rate/i.test(joined) || cellTexts.some((t) => /^rate/i.test(t))) {
      if (colMap.rate === -1) colMap.rate = c;
    }
    if (/taxable value/i.test(joined)) {
      if (colMap.taxableValue === -1) colMap.taxableValue = c;
    }
    if (/integrated tax|igst/i.test(joined)) {
      if (colMap.igst === -1) colMap.igst = c;
    }
    if (/central tax|cgst/i.test(joined)) {
      if (colMap.cgst === -1) colMap.cgst = c;
    }
    if (/state.*tax|sgst|ut tax/i.test(joined)) {
      if (colMap.sgst === -1) colMap.sgst = c;
    }
    if (/cess/i.test(joined)) {
      if (colMap.cess === -1) colMap.cess = c;
    }
    if (/note number/i.test(joined) && !/original/i.test(joined)) {
      if (colMap.noteNumber === -1) colMap.noteNumber = c;
    }
    if (/note type/i.test(joined) && !/original/i.test(joined)) {
      if (colMap.noteType === -1) colMap.noteType = c;
    }
    if (/note date/i.test(joined) && !/original/i.test(joined)) {
      if (colMap.noteDate === -1) colMap.noteDate = c;
    }
    if (/original.*invoice number/i.test(joined)) colMap.origInvNumber = c;
    if (/original.*invoice date/i.test(joined)) colMap.origInvDate = c;
    if (/original.*note number/i.test(joined)) colMap.origNoteNumber = c;
    if (/original.*note date/i.test(joined)) colMap.origNoteDate = c;
  }

  return colMap;
}

/**
 * =========================================================================
 * OPERATION 1: PORTAL TOTAL ROW REMOVAL
 * =========================================================================
 * Filters out portal-generated "-Total" rows and summary rows.
 * Uses detail rows as the single source of truth for rate and amounts.
 */
function classifyAndFilterPortalTotals(rows, dataStart, colMap) {
  const detailRows = [];
  let totalRowsExcluded = 0;

  const docCol = colMap.invNumber !== -1 ? colMap.invNumber : colMap.noteNumber;

  for (let r = dataStart; r < rows.length; r++) {
    const row = rows[r];
    if (!row || !row.some((v) => cleanStr(v) !== '')) continue;

    if (isPortalTotalRow(row, docCol)) {
      totalRowsExcluded++;
      continue;
    }

    detailRows.push(row);
  }

  return { detailRows, totalRowsExcluded };
}

/**
 * =========================================================================
 * OPERATION 2: WITHIN-DOCUMENT DETAIL-LINE AGGREGATION
 * =========================================================================
 * Aggregates only detail lines having the SAME document identity and SAME GST Rate.
 * Invoices with multiple GST rates (e.g. 5% and 18%) remain separate rows.
 */
function aggregateWithinDocumentLines(detailRows, colMap, period) {
  const aggregatedMap = new Map(); // aggregationKey -> aggregatedRow
  let multiRateDocCount = 0;
  const docRateTracker = new Map(); // documentKey -> Set of distinct rates

  for (const row of detailRows) {
    const gstin = colMap.gstin !== -1 ? cleanStr(row[colMap.gstin]).toUpperCase() : '';
    const invNo = colMap.invNumber !== -1 ? cleanStr(row[colMap.invNumber]).toUpperCase() : '';
    const invDate = colMap.invDate !== -1 ? cleanStr(row[colMap.invDate]) : '';
    const invType = colMap.invType !== -1 ? cleanStr(row[colMap.invType]) : '';
    const noteNo = colMap.noteNumber !== -1 ? cleanStr(row[colMap.noteNumber]).toUpperCase() : '';
    const noteType = colMap.noteType !== -1 ? cleanStr(row[colMap.noteType]) : '';
    const pos = colMap.pos !== -1 ? cleanStr(row[colMap.pos]) : '';
    const revChg = colMap.reverseCharge !== -1 ? cleanStr(row[colMap.reverseCharge]) : '';

    const rawRate = colMap.rate !== -1 ? row[colMap.rate] : null;
    const normRate = normalizeRate(rawRate);
    const rateKey = normRate === null ? 'NORATE' : `R${normRate}`;

    // 1. Document Key (Document identity)
    const docKey = `${gstin}|${invNo || noteNo}|${invDate || noteType}|${invType}`;

    // Track distinct rates per document
    if (!docRateTracker.has(docKey)) {
      docRateTracker.set(docKey, new Set());
    }
    docRateTracker.get(docKey).add(rateKey);

    // 2. Aggregation Key (Same document + Same Rate + Same POS + Same Reverse Charge + Period)
    const aggKey = `${docKey}|${pos}|${revChg}|${rateKey}|${period}`;

    if (!aggregatedMap.has(aggKey)) {
      const clonedRow = [...row];
      // Format rate cleanly
      if (colMap.rate !== -1) {
        clonedRow[colMap.rate] = formatCleanRate(rawRate);
      }
      if (colMap.invValue !== -1) clonedRow[colMap.invValue] = normalizeNumeric(row[colMap.invValue]);
      if (colMap.taxableValue !== -1) clonedRow[colMap.taxableValue] = normalizeNumeric(row[colMap.taxableValue]);
      if (colMap.igst !== -1) clonedRow[colMap.igst] = normalizeNumeric(row[colMap.igst]);
      if (colMap.cgst !== -1) clonedRow[colMap.cgst] = normalizeNumeric(row[colMap.cgst]);
      if (colMap.sgst !== -1) clonedRow[colMap.sgst] = normalizeNumeric(row[colMap.sgst]);
      if (colMap.cess !== -1) clonedRow[colMap.cess] = normalizeNumeric(row[colMap.cess]);
      aggregatedMap.set(aggKey, clonedRow);
    } else {
      // Sum tax fields
      const targetRow = aggregatedMap.get(aggKey);

      if (colMap.taxableValue !== -1) {
        targetRow[colMap.taxableValue] =
          normalizeNumeric(targetRow[colMap.taxableValue]) + normalizeNumeric(row[colMap.taxableValue]);
      }
      if (colMap.igst !== -1) {
        targetRow[colMap.igst] =
          normalizeNumeric(targetRow[colMap.igst]) + normalizeNumeric(row[colMap.igst]);
      }
      if (colMap.cgst !== -1) {
        targetRow[colMap.cgst] =
          normalizeNumeric(targetRow[colMap.cgst]) + normalizeNumeric(row[colMap.cgst]);
      }
      if (colMap.sgst !== -1) {
        targetRow[colMap.sgst] =
          normalizeNumeric(targetRow[colMap.sgst]) + normalizeNumeric(row[colMap.sgst]);
      }
      if (colMap.cess !== -1) {
        targetRow[colMap.cess] =
          normalizeNumeric(targetRow[colMap.cess]) + normalizeNumeric(row[colMap.cess]);
      }
      // Note: Invoice Value is NOT summed (remains the invoice-level value)
    }
  }

  for (const [, rates] of docRateTracker) {
    if (rates.size > 1) {
      multiRateDocCount++;
    }
  }

  return {
    aggregatedRows: Array.from(aggregatedMap.values()),
    multiRateDocCount,
  };
}

/**
 * =========================================================================
 * OPERATION 3: CROSS-FILE DUPLICATE DETECTION
 * =========================================================================
 * Eliminates duplicate transaction lines across files without summing duplicate uploads.
 */
function deduplicateAcrossFiles(fileItems, sheetName, lastHeaderRow) {
  const seenKeys = new Set();
  const finalRows = [];
  let duplicatesSkipped = 0;

  for (const { period, row } of fileItems) {
    const dupKey = buildGstr2aRecordKey(sheetName, row, lastHeaderRow, period);
    if (dupKey && seenKeys.has(dupKey)) {
      duplicatesSkipped++;
      continue;
    }
    if (dupKey) seenKeys.add(dupKey);
    finalRows.push([...row, period]);
  }

  return { finalRows, duplicatesSkipped };
}

/**
 * Reconcile control totals between source detail rows and merged output rows
 */
function reconcileControlTotals(sourceDetailRows, mergedOutputRows, colMap, sheetName) {
  const sourceTotals = { taxable: 0, igst: 0, cgst: 0, sgst: 0, cess: 0 };
  const mergedTotals = { taxable: 0, igst: 0, cgst: 0, sgst: 0, cess: 0 };

  for (const row of sourceDetailRows) {
    if (colMap.taxableValue !== -1) sourceTotals.taxable += normalizeNumeric(row[colMap.taxableValue]);
    if (colMap.igst !== -1) sourceTotals.igst += normalizeNumeric(row[colMap.igst]);
    if (colMap.cgst !== -1) sourceTotals.cgst += normalizeNumeric(row[colMap.cgst]);
    if (colMap.sgst !== -1) sourceTotals.sgst += normalizeNumeric(row[colMap.sgst]);
    if (colMap.cess !== -1) sourceTotals.cess += normalizeNumeric(row[colMap.cess]);
  }

  for (const row of mergedOutputRows) {
    if (colMap.taxableValue !== -1) mergedTotals.taxable += normalizeNumeric(row[colMap.taxableValue]);
    if (colMap.igst !== -1) mergedTotals.igst += normalizeNumeric(row[colMap.igst]);
    if (colMap.cgst !== -1) mergedTotals.cgst += normalizeNumeric(row[colMap.cgst]);
    if (colMap.sgst !== -1) mergedTotals.sgst += normalizeNumeric(row[colMap.sgst]);
    if (colMap.cess !== -1) mergedTotals.cess += normalizeNumeric(row[colMap.cess]);
  }

  const diff = {
    taxable: Math.abs(sourceTotals.taxable - mergedTotals.taxable),
    igst: Math.abs(sourceTotals.igst - mergedTotals.igst),
    cgst: Math.abs(sourceTotals.cgst - mergedTotals.cgst),
    sgst: Math.abs(sourceTotals.sgst - mergedTotals.sgst),
    cess: Math.abs(sourceTotals.cess - mergedTotals.cess),
  };

  const isReconciled =
    diff.taxable <= 0.01 &&
    diff.igst <= 0.01 &&
    diff.cgst <= 0.01 &&
    diff.sgst <= 0.01 &&
    diff.cess <= 0.01;

  return { sourceTotals, mergedTotals, diff, isReconciled };
}

export function getCompositeHeaderRow(headerBlock) {
  const numCols = Math.max(...headerBlock.map((r) => (r ? r.length : 0)), 0);
  const composite = [];
  for (let c = 0; c < numCols; c++) {
    const text = headerBlock
      .map((r) => (r && r[c] != null ? cleanStr(r[c]) : ''))
      .filter(Boolean)
      .join(' ');
    composite.push(text);
  }
  return composite;
}

/**
 * Main GSTR-2A Workbook Merger
 */
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

  // 3. Sort files by FY month (April -> March)
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

  // 5. Collect, filter total rows, and aggregate detail rows per sheet
  const sheetCollectedItems = {}; // sheetName -> { period, row }[]
  const sheetAuditLogs = {};

  for (const file of sortedFiles) {
    const period = extractPeriod(file.name);
    const wb = await readWorkbook(file);

    for (const sheetName of wb.SheetNames) {
      if (GSTR2A_SKIP_SHEETS.has(sheetName.trim().toLowerCase())) continue;

      const ws = wb.Sheets[sheetName];
      const rows = sheetTo2DArray(ws);
      if (rows.length === 0) continue;

      const headerEnd = findGstr2aHeaderEnd(rows);
      const headerBlock = rows.slice(0, headerEnd + 1);
      const colMap = buildColumnIndexMap(headerBlock);
      const dataStart = headerEnd + 1;

      // Operation 1: Classify and remove portal total rows
      const { detailRows, totalRowsExcluded } = classifyAndFilterPortalTotals(rows, dataStart, colMap);

      // Operation 2: Within-document detail aggregation
      const { aggregatedRows, multiRateDocCount } = aggregateWithinDocumentLines(detailRows, colMap, period);

      if (!sheetCollectedItems[sheetName]) {
        sheetCollectedItems[sheetName] = [];
        sheetAuditLogs[sheetName] = {
          sourceDetailRows: [],
          totalRowsExcluded: 0,
          multiRateDocCount: 0,
          colMap,
        };
      }

      sheetAuditLogs[sheetName].sourceDetailRows.push(...detailRows);
      sheetAuditLogs[sheetName].totalRowsExcluded += totalRowsExcluded;
      sheetAuditLogs[sheetName].multiRateDocCount += multiRateDocCount;

      for (const aggRow of aggregatedRows) {
        sheetCollectedItems[sheetName].push({ period, row: aggRow });
      }
    }
  }

  // 6. Build final workbook with cross-file duplicate detection (Operation 3)
  const outWb = XLSX.utils.book_new();
  let totalDataRows = 0;
  let duplicateRowsSkipped = 0;

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

    const headerBlock = templateRows.slice(0, headerEnd + 1);
    const compositeHeaders = getCompositeHeaderRow(headerBlock);
    const lastHeaderRow = headerBlock[headerEnd] || [];

    const lastHdr = [...lastHeaderRow];
    lastHdr.push('Source_Period');
    headerBlock[headerEnd] = lastHdr;

    const items = sheetCollectedItems[sheetName] || [];
    const { finalRows, duplicatesSkipped } = deduplicateAcrossFiles(items, sheetName, compositeHeaders);
    duplicateRowsSkipped += duplicatesSkipped;
    totalDataRows += finalRows.length;

    // Reconciliation Check
    if (sheetAuditLogs[sheetName]) {
      const recon = reconcileControlTotals(
        sheetAuditLogs[sheetName].sourceDetailRows,
        finalRows,
        sheetAuditLogs[sheetName].colMap,
        sheetName,
      );
      if (!recon.isReconciled) {
        console.warn(`[Reconciliation Warning] GSTR-2A sheet [${sheetName}] monetary mismatch:`, recon.diff);
      }
    }

    const finalSheetRows = [...headerBlock, ...finalRows];
    const newWs = XLSX.utils.aoa_to_sheet(finalSheetRows);
    XLSX.utils.book_append_sheet(outWb, newWs, sheetName);
  }

  // 7. Append GST_AUDIT_META sheet marker
  const metaWs = createMergeMetadataSheet({
    mergeType: 'GSTR2A',
    gstin: dealer.gstin || '',
    legalName: dealer.legal_name || '',
    financialYear: dealer.financial_year || '',
    sourceFileCount: filenames.length,
    sourceFiles: filenames,
    totalRows: totalDataRows,
  });
  XLSX.utils.book_append_sheet(outWb, metaWs, META_SHEET_NAME);

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
    row_count: totalDataRows,
    duplicate_rows_skipped: duplicateRowsSkipped,
  };
}
