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
  normalizeRate,
  formatCleanRate,
  normalizeNumeric,
  isPortalTotalRow,
} from './excelUtils.js';
import { extractDealerMetadataFromFiles } from './dealerMetadataService.js';
import {
  buildGstr1RecordKey,
  createMergeMetadataSheet,
  META_SHEET_NAME,
} from './duplicateDetection.js';

const GSTR1_SKIP_SHEETS = new Set(['read me', 'readme', 'gst_audit_meta']);
const GSTR1_HEADER_ROW_INDEX = 3; // 0-based row 3 = Excel Row 4

/**
 * Helper to identify column indexes from GSTR-1 header row
 */
function buildGstr1ColumnMap(headers) {
  const colMap = {
    gstin: -1,
    receiverName: -1,
    invNumber: -1,
    invDate: -1,
    invValue: -1,
    pos: -1,
    reverseCharge: -1,
    invType: -1,
    rate: -1,
    taxableValue: -1,
    igst: -1,
    cgst: -1,
    sgst: -1,
    cess: -1,
    noteNumber: -1,
    noteDate: -1,
    noteType: -1,
    noteSupplyType: -1,
    noteValue: -1,
    hsn: -1,
    description: -1,
    uqc: -1,
    totalQty: -1,
    docNature: -1,
    srFrom: -1,
    srTo: -1,
    totalDocs: -1,
    cancelledDocs: -1,
    nilSupplies: -1,
    exemptSupplies: -1,
    nonGstSupplies: -1,
    grossAdvance: -1,
  };

  headers.forEach((h, c) => {
    const text = cleanStr(h).toLowerCase();
    if (!text) return;

    if (/gstin|uin/i.test(text)) colMap.gstin = c;
    if (/receiver name/i.test(text)) colMap.receiverName = c;
    if (/invoice number|inv no/i.test(text) && !/original/i.test(text)) colMap.invNumber = c;
    if (/invoice date/i.test(text) && !/original/i.test(text)) colMap.invDate = c;
    if (/invoice value/i.test(text)) colMap.invValue = c;
    if (/place of supply/i.test(text)) colMap.pos = c;
    if (/reverse charge/i.test(text)) colMap.reverseCharge = c;
    if (/invoice type/i.test(text)) colMap.invType = c;
    if (/^rate$|^rate\s*\(|gst rate/i.test(text)) colMap.rate = c;
    if (/taxable value|taxable val/i.test(text)) colMap.taxableValue = c;
    if (/integrated tax|igst/i.test(text)) colMap.igst = c;
    if (/central tax|cgst/i.test(text)) colMap.cgst = c;
    if (/state.*tax|sgst|ut tax/i.test(text)) colMap.sgst = c;
    if (/cess/i.test(text)) colMap.cess = c;
    if (/note number/i.test(text) && !/original/i.test(text)) colMap.noteNumber = c;
    if (/note date/i.test(text) && !/original/i.test(text)) colMap.noteDate = c;
    if (/note type/i.test(text) && !/original/i.test(text)) colMap.noteType = c;
    if (/note supply type/i.test(text)) colMap.noteSupplyType = c;
    if (/note value/i.test(text)) colMap.noteValue = c;
    if (/^hsn/i.test(text)) colMap.hsn = c;
    if (/description/i.test(text)) colMap.description = c;
    if (/uqc/i.test(text)) colMap.uqc = c;
    if (/total quantity/i.test(text)) colMap.totalQty = c;
    if (/nature of document/i.test(text)) colMap.docNature = c;
    if (/sr\.?\s*no\.?\s*from/i.test(text)) colMap.srFrom = c;
    if (/sr\.?\s*no\.?\s*to/i.test(text)) colMap.srTo = c;
    if (/total number/i.test(text)) colMap.totalDocs = c;
    if (/cancelled/i.test(text)) colMap.cancelledDocs = c;
    if (/nil rated supplies/i.test(text)) colMap.nilSupplies = c;
    if (/exempted/i.test(text)) colMap.exemptSupplies = c;
    if (/non-gst supplies/i.test(text)) colMap.nonGstSupplies = c;
    if (/gross advance/i.test(text)) colMap.grossAdvance = c;
  });

  return colMap;
}

/**
 * =========================================================================
 * OPERATION 1 & 2: GSTR-1 DETAIL FILTERING & WITHIN-DOCUMENT AGGREGATION
 * =========================================================================
 */
function processGstr1SheetRows(sheetName, rawDataRows, colMap, period) {
  const sheetLower = sheetName.trim().toLowerCase();
  const detailRows = [];
  let totalRowsExcluded = 0;

  const docCol = colMap.invNumber !== -1 ? colMap.invNumber : colMap.noteNumber;

  // Operation 1: Remove any portal total rows if present
  for (const row of rawDataRows) {
    if (!row || !row.some((v) => cleanStr(v) !== '')) continue;

    if (isPortalTotalRow(row, docCol)) {
      totalRowsExcluded++;
      continue;
    }
    detailRows.push(row);
  }

  // Operation 2: Aggregate within document / transaction grain
  const aggregatedMap = new Map();
  let multiRateDocCount = 0;
  const docRateTracker = new Map();

  let curGstin = '';
  let curInvNo = '';
  let curInvDate = '';
  let curInvType = '';
  let curNoteNo = '';
  let curNoteDate = '';
  let curNoteType = '';
  let curPos = '';
  let curRevChg = '';

  for (const row of detailRows) {
    const rawGstin = colMap.gstin !== -1 ? cleanStr(row[colMap.gstin]).toUpperCase() : '';
    const rawInvNo = colMap.invNumber !== -1 ? cleanStr(row[colMap.invNumber]).toUpperCase() : '';
    const rawNoteNo = colMap.noteNumber !== -1 ? cleanStr(row[colMap.noteNumber]).toUpperCase() : '';

    if (rawGstin) curGstin = rawGstin;
    if (rawInvNo) curInvNo = rawInvNo;
    if (rawNoteNo) curNoteNo = rawNoteNo;
    if (colMap.invDate !== -1 && cleanStr(row[colMap.invDate])) curInvDate = cleanStr(row[colMap.invDate]);
    if (colMap.invType !== -1 && cleanStr(row[colMap.invType])) curInvType = cleanStr(row[colMap.invType]);
    if (colMap.noteDate !== -1 && cleanStr(row[colMap.noteDate])) curNoteDate = cleanStr(row[colMap.noteDate]);
    if (colMap.noteType !== -1 && cleanStr(row[colMap.noteType])) curNoteType = cleanStr(row[colMap.noteType]);
    if (colMap.pos !== -1 && cleanStr(row[colMap.pos])) curPos = cleanStr(row[colMap.pos]);
    if (colMap.reverseCharge !== -1 && cleanStr(row[colMap.reverseCharge])) curRevChg = cleanStr(row[colMap.reverseCharge]);

    const gstin = rawGstin || curGstin;
    const invNo = rawInvNo || curInvNo;
    const invDate = (colMap.invDate !== -1 && cleanStr(row[colMap.invDate])) ? cleanStr(row[colMap.invDate]) : curInvDate;
    const invType = (colMap.invType !== -1 && cleanStr(row[colMap.invType])) ? cleanStr(row[colMap.invType]) : curInvType;
    const noteNo = rawNoteNo || curNoteNo;
    const noteDate = (colMap.noteDate !== -1 && cleanStr(row[colMap.noteDate])) ? cleanStr(row[colMap.noteDate]) : curNoteDate;
    const noteType = (colMap.noteType !== -1 && cleanStr(row[colMap.noteType])) ? cleanStr(row[colMap.noteType]) : curNoteType;
    const pos = (colMap.pos !== -1 && cleanStr(row[colMap.pos])) ? cleanStr(row[colMap.pos]) : curPos;
    const revChg = (colMap.reverseCharge !== -1 && cleanStr(row[colMap.reverseCharge])) ? cleanStr(row[colMap.reverseCharge]) : curRevChg;

    const hsn = colMap.hsn !== -1 ? cleanStr(row[colMap.hsn]) : '';
    const uqc = colMap.uqc !== -1 ? cleanStr(row[colMap.uqc]) : '';
    const desc = colMap.description !== -1 ? cleanStr(row[colMap.description]) : '';
    const docNature = colMap.docNature !== -1 ? cleanStr(row[colMap.docNature]) : '';
    const srFrom = colMap.srFrom !== -1 ? cleanStr(row[colMap.srFrom]) : '';
    const srTo = colMap.srTo !== -1 ? cleanStr(row[colMap.srTo]) : '';

    const rawRate = colMap.rate !== -1 ? row[colMap.rate] : null;
    const normRate = normalizeRate(rawRate);
    const rateKey = normRate === null ? 'NORATE' : `R${normRate}`;

    let docKey = '';
    let aggKey = '';

    if (sheetLower.includes('b2b') || sheetLower.includes('b2cl') || sheetLower.includes('exp')) {
      docKey = `${gstin}|${invNo}|${invDate}|${invType}`;
      aggKey = `${docKey}|${pos}|${revChg}|${rateKey}|${period}`;
    } else if (sheetLower.includes('cdnr') || sheetLower.includes('cdnur')) {
      docKey = `${gstin}|${noteNo}|${noteDate}|${noteType}`;
      aggKey = `${docKey}|${pos}|${revChg}|${rateKey}|${period}`;
    } else if (sheetLower.includes('b2cs')) {
      docKey = `${pos}|${rateKey}`;
      aggKey = `${docKey}|${period}`;
    } else if (sheetLower.includes('exemp')) {
      docKey = `${desc}`;
      aggKey = `${docKey}|${period}`;
    } else if (sheetLower.includes('hsn')) {
      docKey = `${hsn}|${desc}|${uqc}|${rateKey}`;
      aggKey = `${docKey}|${period}`;
    } else if (sheetLower.includes('docs')) {
      docKey = `${docNature}|${srFrom}|${srTo}`;
      aggKey = `${docKey}|${period}`;
    } else if (sheetLower.includes('at')) {
      docKey = `${pos}|${rateKey}`;
      aggKey = `${docKey}|${period}`;
    } else {
      // Generic fallback: full normalized row content + period
      docKey = row.map(cleanStr).join('|');
      aggKey = `${docKey}|${period}`;
    }

    if (docKey) {
      if (!docRateTracker.has(docKey)) docRateTracker.set(docKey, new Set());
      docRateTracker.get(docKey).add(rateKey);
    }

    if (!aggregatedMap.has(aggKey)) {
      const clonedRow = [...row];
      if (colMap.gstin !== -1 && gstin) clonedRow[colMap.gstin] = gstin;
      if (colMap.invNumber !== -1 && invNo) clonedRow[colMap.invNumber] = invNo;
      if (colMap.invDate !== -1 && invDate) clonedRow[colMap.invDate] = invDate;
      if (colMap.invType !== -1 && invType) clonedRow[colMap.invType] = invType;
      if (colMap.noteNumber !== -1 && noteNo) clonedRow[colMap.noteNumber] = noteNo;
      if (colMap.noteDate !== -1 && noteDate) clonedRow[colMap.noteDate] = noteDate;
      if (colMap.noteType !== -1 && noteType) clonedRow[colMap.noteType] = noteType;
      if (colMap.pos !== -1 && pos) clonedRow[colMap.pos] = pos;
      if (colMap.reverseCharge !== -1 && revChg) clonedRow[colMap.reverseCharge] = revChg;
      if (colMap.rate !== -1) {
        clonedRow[colMap.rate] = formatCleanRate(rawRate);
      }
      if (colMap.invValue !== -1) clonedRow[colMap.invValue] = normalizeNumeric(row[colMap.invValue]);
      if (colMap.taxableValue !== -1) clonedRow[colMap.taxableValue] = normalizeNumeric(row[colMap.taxableValue]);
      if (colMap.igst !== -1) clonedRow[colMap.igst] = normalizeNumeric(row[colMap.igst]);
      if (colMap.cgst !== -1) clonedRow[colMap.cgst] = normalizeNumeric(row[colMap.cgst]);
      if (colMap.sgst !== -1) clonedRow[colMap.sgst] = normalizeNumeric(row[colMap.sgst]);
      if (colMap.cess !== -1) clonedRow[colMap.cess] = normalizeNumeric(row[colMap.cess]);
      if (colMap.totalQty !== -1) clonedRow[colMap.totalQty] = normalizeNumeric(row[colMap.totalQty]);
      if (colMap.nilSupplies !== -1) clonedRow[colMap.nilSupplies] = normalizeNumeric(row[colMap.nilSupplies]);
      if (colMap.exemptSupplies !== -1) clonedRow[colMap.exemptSupplies] = normalizeNumeric(row[colMap.exemptSupplies]);
      if (colMap.nonGstSupplies !== -1) clonedRow[colMap.nonGstSupplies] = normalizeNumeric(row[colMap.nonGstSupplies]);
      if (colMap.grossAdvance !== -1) clonedRow[colMap.grossAdvance] = normalizeNumeric(row[colMap.grossAdvance]);
      aggregatedMap.set(aggKey, clonedRow);
    } else {
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
      if (colMap.totalQty !== -1) {
        targetRow[colMap.totalQty] =
          normalizeNumeric(targetRow[colMap.totalQty]) + normalizeNumeric(row[colMap.totalQty]);
      }
      if (colMap.nilSupplies !== -1) {
        targetRow[colMap.nilSupplies] =
          normalizeNumeric(targetRow[colMap.nilSupplies]) + normalizeNumeric(row[colMap.nilSupplies]);
      }
      if (colMap.exemptSupplies !== -1) {
        targetRow[colMap.exemptSupplies] =
          normalizeNumeric(targetRow[colMap.exemptSupplies]) + normalizeNumeric(row[colMap.exemptSupplies]);
      }
      if (colMap.nonGstSupplies !== -1) {
        targetRow[colMap.nonGstSupplies] =
          normalizeNumeric(targetRow[colMap.nonGstSupplies]) + normalizeNumeric(row[colMap.nonGstSupplies]);
      }
      if (colMap.grossAdvance !== -1) {
        targetRow[colMap.grossAdvance] =
          normalizeNumeric(targetRow[colMap.grossAdvance]) + normalizeNumeric(row[colMap.grossAdvance]);
      }
    }
  }

  for (const [, rates] of docRateTracker) {
    if (rates.size > 1) multiRateDocCount++;
  }

  return {
    detailRows,
    aggregatedRows: Array.from(aggregatedMap.values()),
    totalRowsExcluded,
    multiRateDocCount,
  };
}

/**
 * =========================================================================
 * OPERATION 3: CROSS-FILE DUPLICATE DETECTION FOR GSTR-1
 * =========================================================================
 */
function deduplicateGstr1AcrossFiles(fileItems, sheetName, headers) {
  const seenKeys = new Set();
  const finalRows = [];
  let duplicatesSkipped = 0;

  for (const { period, row } of fileItems) {
    const dupKey = buildGstr1RecordKey(sheetName, row, headers, period);
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
 * Reconcile control totals for GSTR-1
 */
function reconcileGstr1ControlTotals(sourceDetailRows, mergedOutputRows, colMap, sheetName) {
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

/**
 * Main GSTR-1 Workbook Merger
 */
export async function mergeGstr1Files(files, options = {}) {
  if (!files || files.length === 0) {
    throw new Error('No files provided for merging.');
  }

  // 1. Dealer consistency & metadata
  const meta = await extractDealerMetadataFromFiles(files, 'gstr1');
  const dealer = meta.dealer;

  // 2. Missing months detection
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

  // 4. Load first file as template workbook
  const templateWb = await readWorkbook(sortedFiles[0]);

  // 5. Collect rows per sheet across all files
  const sheetCollectedItems = {}; // sheetName -> { period, row }[]
  const sheetAuditLogs = {};
  const sheetHeadersMap = {};

  for (const file of sortedFiles) {
    const period = extractPeriod(file.name);
    const wb = await readWorkbook(file);

    for (const sheetName of wb.SheetNames) {
      if (GSTR1_SKIP_SHEETS.has(sheetName.trim().toLowerCase())) continue;

      const ws = wb.Sheets[sheetName];
      const rawRows = sheetTo2DArray(ws);

      if (rawRows.length <= GSTR1_HEADER_ROW_INDEX) continue;

      const headerRow = rawRows[GSTR1_HEADER_ROW_INDEX] || [];
      const colMap = buildGstr1ColumnMap(headerRow);
      sheetHeadersMap[sheetName] = headerRow;

      const rawDataRows = rawRows.slice(GSTR1_HEADER_ROW_INDEX + 1);

      const { detailRows, aggregatedRows, totalRowsExcluded, multiRateDocCount } =
        processGstr1SheetRows(sheetName, rawDataRows, colMap, period);

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

    if (GSTR1_SKIP_SHEETS.has(lowerName)) {
      const srcSheet = templateWb.Sheets[sheetName];
      const readmeRows = sheetTo2DArray(srcSheet);

      // Row 4 (Excel row 5, 0-based idx 4), Col C (0-based idx 2) is tax period
      if (readmeRows[4]) readmeRows[4][2] = taxPeriodText;
      if (readmeRows[8]) readmeRows[8][2] = '';
      if (readmeRows[9]) readmeRows[9][2] = '';

      const patchedSheet = XLSX.utils.aoa_to_sheet(readmeRows);
      XLSX.utils.book_append_sheet(outWb, patchedSheet, sheetName);
      continue;
    }

    const templateSheet = templateWb.Sheets[sheetName];
    const templateRows = sheetTo2DArray(templateSheet);

    const topRows = templateRows.slice(0, GSTR1_HEADER_ROW_INDEX);
    const origHeader = templateRows[GSTR1_HEADER_ROW_INDEX] || sheetHeadersMap[sheetName] || [];
    const finalHeader = [...origHeader, 'Source_Period'];

    const items = sheetCollectedItems[sheetName] || [];
    const { finalRows, duplicatesSkipped } = deduplicateGstr1AcrossFiles(items, sheetName, origHeader);
    duplicateRowsSkipped += duplicatesSkipped;
    totalDataRows += finalRows.length;

    // Reconciliation Check
    if (sheetAuditLogs[sheetName]) {
      const recon = reconcileGstr1ControlTotals(
        sheetAuditLogs[sheetName].sourceDetailRows,
        finalRows,
        sheetAuditLogs[sheetName].colMap,
        sheetName,
      );
      if (!recon.isReconciled) {
        console.warn(`[Reconciliation Warning] GSTR-1 sheet [${sheetName}] monetary mismatch:`, recon.diff);
      }
    }

    const finalSheetRows = [...topRows, finalHeader, ...finalRows];
    const newWs = XLSX.utils.aoa_to_sheet(finalSheetRows);
    XLSX.utils.book_append_sheet(outWb, newWs, sheetName);
  }

  // 7. Append GST_AUDIT_META sheet marker
  const metaWs = createMergeMetadataSheet({
    mergeType: 'GSTR1',
    gstin: dealer.gstin || '',
    legalName: dealer.legal_name || '',
    financialYear: dealer.financial_year || '',
    sourceFileCount: filenames.length,
    sourceFiles: filenames,
    totalRows: totalDataRows,
  });
  XLSX.utils.book_append_sheet(outWb, metaWs, META_SHEET_NAME);

  // Output filename
  let autoName = 'GSTR1_Merged.xlsx';
  if (dealer.gstin && dealer.financial_year) {
    const safeGstin = dealer.gstin.replace(/[\\/:*?"<>|]/g, '_');
    const safeFy = dealer.financial_year.replace(/[\\/:*?"<>|]/g, '_');
    autoName = `GSTR1_${safeGstin}_${safeFy}_Merged.xlsx`;
  }

  const blob = workbookToBlob(outWb);

  return {
    blob,
    suggested_filename: autoName,
    missing_months: missingMonths,
    dealer,
    workbook_id: meta.workbook_id,
    return_type: 'gstr1',
    source_files: filenames,
    sheet_list: outWb.SheetNames,
    row_count: totalDataRows,
    duplicate_rows_skipped: duplicateRowsSkipped,
  };
}
