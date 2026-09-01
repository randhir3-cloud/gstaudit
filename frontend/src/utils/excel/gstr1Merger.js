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
} from './excelUtils';
import { extractDealerMetadataFromFiles } from './dealerMetadataService';

const GSTR1_SKIP_SHEETS = new Set(['read me', 'readme']);
const GSTR1_HEADER_ROW_INDEX = 3; // 0-based row 3 = Excel Row 4

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
  const sheetData = {}; // sheetName -> { headers: string[], rows: any[][] }

  for (const file of sortedFiles) {
    const period = extractPeriod(file.name);
    const wb = await readWorkbook(file);

    for (const sheetName of wb.SheetNames) {
      if (GSTR1_SKIP_SHEETS.has(sheetName.trim().toLowerCase())) continue;

      const ws = wb.Sheets[sheetName];
      const rawRows = sheetTo2DArray(ws);

      if (rawRows.length <= GSTR1_HEADER_ROW_INDEX) continue;

      const headerRow = rawRows[GSTR1_HEADER_ROW_INDEX] || [];
      const dataRows = rawRows.slice(GSTR1_HEADER_ROW_INDEX + 1);

      if (!sheetData[sheetName]) {
        sheetData[sheetName] = {
          headers: headerRow.map((h) => cleanStr(h)),
          rows: [],
        };
      }

      // Append data rows with Source_Period
      for (const row of dataRows) {
        // Check if row has any non-empty data
        const hasData = row.some((val) => cleanStr(val) !== '');
        if (hasData) {
          sheetData[sheetName].rows.push([...row, period]);
        }
      }
    }
  }

  // 6. Build final workbook from template
  const outWb = XLSX.utils.book_new();

  for (const sheetName of templateWb.SheetNames) {
    const lowerName = sheetName.trim().toLowerCase();

    if (GSTR1_SKIP_SHEETS.has(lowerName)) {
      // Patch Read me sheet with updated tax period
      const srcSheet = templateWb.Sheets[sheetName];
      const readmeRows = sheetTo2DArray(srcSheet);

      // Row 4 (Excel row 5, 0-based idx 4), Col C (0-based idx 2) is tax period
      if (readmeRows[4]) readmeRows[4][2] = taxPeriodText;
      // Clear ARN and ARN Date
      if (readmeRows[8]) readmeRows[8][2] = '';
      if (readmeRows[9]) readmeRows[9][2] = '';

      const patchedSheet = XLSX.utils.aoa_to_sheet(readmeRows);
      XLSX.utils.book_append_sheet(outWb, patchedSheet, sheetName);
      continue;
    }

    if (!sheetData[sheetName]) {
      // Keep original sheet from template if no data collected
      XLSX.utils.book_append_sheet(outWb, templateWb.Sheets[sheetName], sheetName);
      continue;
    }

    // Sheet headers + Source_Period column
    const templateSheet = templateWb.Sheets[sheetName];
    const templateRows = sheetTo2DArray(templateSheet);

    // Keep top metadata/blank rows before header
    const topRows = templateRows.slice(0, GSTR1_HEADER_ROW_INDEX);
    const origHeader = templateRows[GSTR1_HEADER_ROW_INDEX] || sheetData[sheetName].headers;
    const finalHeader = [...origHeader, 'Source_Period'];

    const finalSheetRows = [...topRows, finalHeader, ...sheetData[sheetName].rows];
    const newWs = XLSX.utils.aoa_to_sheet(finalSheetRows);
    XLSX.utils.book_append_sheet(outWb, newWs, sheetName);
  }

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
  };
}
