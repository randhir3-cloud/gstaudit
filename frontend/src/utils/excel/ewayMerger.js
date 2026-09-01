import * as XLSX from 'xlsx';
import {
  readWorkbookRaw,
  sheetTo2DArray,
  workbookToBlob,
  fileFyKey,
  extractPeriod,
  findMissingMonths,
  MONTH_MAP,
  cleanStr,
} from './excelUtils.js';
import { classifyEwayFiles } from './ewayDetector.js';

function findEwayDateColIndex(headers) {
  for (let i = 0; i < headers.length; i++) {
    const text = cleanStr(headers[i]).toLowerCase().replace(/\n/g, ' ').replace(/\s+/g, ' ');
    if (text.includes('ewb') && (text.includes('dt') || text.includes('date'))) {
      return i;
    }
  }
  if (headers.length > 5) return 5;
  return -1;
}

function parseEwaySourcePeriod(val) {
  if (val == null) return '';
  const text = cleanStr(val);
  if (!text) return '';

  const dateText = text.includes(' - ') ? text.split(' - ')[1].trim() : text;
  const firstPart = dateText.includes(' ') ? dateText.split(' ')[0] : dateText;

  // Formats: DD/MM/YYYY or DD-MM-YYYY
  const m = firstPart.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})$/);
  if (m) {
    const mm = String(m[2]).padStart(2, '0');
    const yyyy = m[3].length === 2 ? `20${m[3]}` : m[3];
    return `${MONTH_MAP[mm] || mm}-${yyyy}`;
  }

  return '';
}

export async function mergeEwayFiles(files, direction = 'outward', options = {}) {
  if (!files || files.length === 0) {
    throw new Error('No E-Way Bill files provided for merging.');
  }

  // 1. Classify all files to confirm direction & dealer
  const classResp = await classifyEwayFiles(files, {
    dealerGstin: options.dealerGstin,
    expectedDirection: direction,
  });

  const wrongFiles = classResp.classifications.filter((c) => c.status === 'wrong_section');
  if (wrongFiles.length > 0) {
    const wrongNames = wrongFiles.map((f) => f.filename).join(', ');
    const err = new Error(`The selected files contain mixed directions. Files (${wrongNames}) are not ${direction}. Please merge one type at a time.`);
    err.payload = {
      error_type: 'direction_mismatch',
      wrong_files: wrongFiles,
    };
    throw err;
  }

  // 2. Check missing months
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

  // 4. Collect rows across all sheets in all files
  let masterHeaders = null;
  let masterRows = [];
  let dateColIdx = -1;

  for (const file of sortedFiles) {
    const periodFromName = extractPeriod(file.name);
    const wb = await readWorkbookRaw(file);

    for (const sheetName of wb.SheetNames) {
      const rows = sheetTo2DArray(wb.Sheets[sheetName]);
      if (rows.length === 0) continue;

      // Header row
      const headers = rows[0] || [];
      if (!masterHeaders) {
        masterHeaders = [...headers.map((h) => cleanStr(h)), 'Source_Period', 'Source_File', 'Source_Sheet', 'EWB_Direction'];
        dateColIdx = findEwayDateColIndex(headers);
      }

      const dataRows = rows.slice(1);
      for (const row of dataRows) {
        if (!row.some((val) => cleanStr(val) !== '')) continue;

        let srcPeriod = '';
        if (dateColIdx !== -1 && row[dateColIdx]) {
          srcPeriod = parseEwaySourcePeriod(row[dateColIdx]);
        }
        if (!srcPeriod) srcPeriod = periodFromName;

        masterRows.push([
          ...row,
          srcPeriod,
          file.name,
          sheetName,
          direction.charAt(0).toUpperCase() + direction.slice(1),
        ]);
      }
    }
  }

  if (!masterHeaders || masterRows.length === 0) {
    throw new Error('No data rows found across uploaded E-Way Bill files.');
  }

  // 5. Build output workbook
  const outWb = XLSX.utils.book_new();
  const allSheetData = [masterHeaders, ...masterRows];
  const outWs = XLSX.utils.aoa_to_sheet(allSheetData);
  const outSheetName = direction === 'inward' ? 'EWB_Inward' : 'EWB_Outward';
  XLSX.utils.book_append_sheet(outWb, outWs, outSheetName);

  const suggestedFilename = direction === 'inward' ? 'EWB_Inward_Merged.xlsx' : 'EWB_Outward_Merged.xlsx';
  const blob = workbookToBlob(outWb);

  const dealerGstin = classResp.dealer_resolution.gstin || options.dealerGstin || '';
  const legalName = classResp.dealer_resolution.legal_name || '';
  const financialYear = classResp.dealer_resolution.financial_year || classResp.classifications[0]?.financial_year || '';

  return {
    blob,
    suggested_filename: suggestedFilename,
    missing_months: missingMonths,
    row_count: masterRows.length,
    sheet_list: [outSheetName],
    source_files: filenames,
    financial_year: financialYear,
    dealer: {
      gstin: dealerGstin,
      legal_name: legalName,
      trade_name: legalName,
      financial_year: financialYear,
      tax_period: '',
    },
    uploaded_months: filenames.map((name) => extractPeriod(name)),
  };
}
