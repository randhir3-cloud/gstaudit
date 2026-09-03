import { readWorkbook, sheetTo2DArray, cleanStr } from './excelUtils.js';

const README_SHEET_NAMES = new Set(['read me', 'readme', 'read_me']);

const FIELD_ALIASES = {
  gstin: ['gstin', "taxpayer's gstin", 'taxpayers gstin', 'taxpayer gstin'],
  legal_name: ['legal name', 'legal name of taxpayer', 'legalname'],
  trade_name: ['trade name', 'trade name (if any)', 'tradename'],
  financial_year: ['financial year', 'financialyear', 'fy'],
  tax_period: ['tax period', 'tax period ', 'taxperiod'],
  arn: ['arn'],
  arn_date: ['arn date'],
  download_date: [
    'date and time of generation',
    'date of generation',
    'download date',
    'date of download',
  ],
};

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

const MONTH_NAME_MAP = {
  january: 1, jan: 1, '01': 1, '1': 1,
  february: 2, feb: 2, '02': 2, '2': 2,
  march: 3, mar: 3, '03': 3, '3': 3,
  april: 4, apr: 4, '04': 4, '4': 4,
  may: 5, '05': 5, '5': 5,
  june: 6, jun: 6, '06': 6, '6': 6,
  july: 7, jul: 7, '07': 7, '7': 7,
  august: 8, aug: 8, '08': 8, '8': 8,
  september: 9, sep: 9, sept: 9, '09': 9, '9': 9,
  october: 10, oct: 10, '10': 10,
  november: 11, nov: 11, '11': 11,
  december: 12, dec: 12, '12': 12,
};

const GSTR1_FALLBACK = {
  financial_year: [3, 2], // 0-based row 3 (Excel 4), col 2 (Excel C)
  tax_period: [4, 2],
  gstin: [5, 2],
  legal_name: [6, 2],
  trade_name: [7, 2],
  arn: [8, 2],
  arn_date: [9, 2],
  download_date: [10, 2],
};

const GSTR2A_FALLBACK = {
  gstin: [1, 2], // row 2, col C
  legal_name: [2, 2],
  trade_name: [3, 2],
  tax_period: [1, 4], // row 2, col E
  financial_year: [2, 4], // row 3, col E
  download_date: [3, 4],
};

export function normalizeMetadataLabel(text) {
  if (text == null) return '';
  return String(text).trim().toLowerCase().replace(/\s+/g, ' ');
}

export function matchMetadataField(label) {
  const normalized = normalizeMetadataLabel(label);
  if (!normalized) return null;
  for (const [field, aliases] of Object.entries(FIELD_ALIASES)) {
    for (const alias of aliases) {
      if (normalized === alias || normalized.includes(alias) || alias.includes(normalized)) {
        return field;
      }
    }
  }
  return null;
}

/**
 * Parses financial year string like '2022-23' or '2022-2023' into { startYear, endYear, raw }
 */
export function parseFinancialYear(rawFy) {
  const text = cleanStr(rawFy);
  if (!text) return { startYear: null, endYear: null, raw: '' };
  
  const m = text.match(/^(\d{4})[-/](\d{2,4})$/);
  if (m) {
    const startYear = parseInt(m[1], 10);
    let endYear = parseInt(m[2], 10);
    if (endYear < 100) {
      endYear = Math.floor(startYear / 100) * 100 + endYear;
    }
    const shortEnd = String(endYear).slice(-2);
    return {
      startYear,
      endYear,
      raw: `${startYear}-${shortEnd}`,
    };
  }
  return { startYear: null, endYear: null, raw: text };
}

/**
 * Parses GSTR-2A Tax Period (MMYYYY or numeric like 042022, 12023) into { month, year, display }
 */
export function parseGstr2aTaxPeriod(rawPeriod, financialYear = '') {
  if (rawPeriod == null) return { month: null, year: null, display: '', raw: '' };
  let str = String(rawPeriod).trim();
  if (!str) return { month: null, year: null, display: '', raw: '' };

  // Handle numeric like 12023 (5 digits) -> '012023'
  if (/^\d{5}$/.test(str)) {
    str = '0' + str;
  }

  // MMYYYY
  if (/^\d{6}$/.test(str)) {
    const month = parseInt(str.slice(0, 2), 10);
    const year = parseInt(str.slice(2), 10);
    if (month >= 1 && month <= 12) {
      const monthName = MONTH_NAMES[month - 1];
      return {
        month,
        year,
        display: `${monthName}-${year}`,
        raw: str,
      };
    }
  }

  // If already month name, delegate to GSTR-1 style
  return parseGstr1TaxPeriod(rawPeriod, financialYear);
}

/**
 * Parses GSTR-1 Tax Period (e.g. 'January', 'April') using Financial Year to resolve the year
 */
export function parseGstr1TaxPeriod(rawPeriod, financialYear = '') {
  if (rawPeriod == null) return { month: null, year: null, display: '', raw: '' };
  const str = String(rawPeriod).trim();
  if (!str) return { month: null, year: null, display: '', raw: '' };

  // If MMYYYY format was passed in GSTR-1
  if (/^\d{5,6}$/.test(str)) {
    return parseGstr2aTaxPeriod(str, financialYear);
  }

  const cleanMonthKey = str.toLowerCase().replace(/[^a-z0-9]/g, '');
  const month = MONTH_NAME_MAP[cleanMonthKey];

  if (month) {
    const monthName = MONTH_NAMES[month - 1];
    const fyInfo = parseFinancialYear(financialYear);
    let year = null;

    if (fyInfo.startYear && fyInfo.endYear) {
      // April (4) to December (12) belongs to startYear; January (1) to March (3) belongs to endYear
      year = month >= 4 ? fyInfo.startYear : fyInfo.endYear;
    }

    const display = year ? `${monthName}-${year}` : monthName;
    return {
      month,
      year,
      display,
      raw: str,
    };
  }

  // If format is 'Month-YYYY' or 'Month YYYY'
  const myMatch = str.match(/^([A-Za-z]+)[-\s](\d{4})$/);
  if (myMatch) {
    const mKey = myMatch[1].toLowerCase();
    const m = MONTH_NAME_MAP[mKey];
    const y = parseInt(myMatch[2], 10);
    if (m) {
      return {
        month: m,
        year: y,
        display: `${MONTH_NAMES[m - 1]}-${y}`,
        raw: str,
      };
    }
  }

  return { month: null, year: null, display: str, raw: str };
}

/**
 * Build chronological range display from an array of normalized period objects:
 * e.g. 'April-2022 to March-2023' or 'April-2022 to June-2022' or 'April-2022'
 */
export function buildTaxPeriodRangeDisplay(periodObjects) {
  const validPeriods = periodObjects.filter((p) => p && p.month && p.year);
  if (validPeriods.length === 0) {
    const rawDisplays = periodObjects.map((p) => p?.display || p?.raw).filter(Boolean);
    return rawDisplays[0] || '';
  }

  // Sort chronologically by year then month
  const sorted = [...validPeriods].sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return a.month - b.month;
  });

  const first = sorted[0];
  const last = sorted[sorted.length - 1];

  if (first.year === last.year && first.month === last.month) {
    return first.display;
  }

  return `${first.display} to ${last.display}`;
}

export function extractDealerMetadataFromSheet(rows, returnType) {
  const found = {};
  const maxRows = Math.min(rows.length, 25);

  for (let r = 0; r < maxRows; r++) {
    const row = rows[r] || [];
    const maxCols = Math.min(row.length, 10);
    for (let c = 0; c < maxCols; c++) {
      const cellVal = row[c];
      const field = matchMetadataField(cellVal);
      if (!field || found[field]) continue;

      // Scan right for value
      for (let vc = c + 1; vc < maxCols; vc++) {
        const val = cleanStr(row[vc]);
        if (!val) continue;
        if (matchMetadataField(val)) break;
        found[field] = val;
        break;
      }
    }
  }

  // Apply positional fallbacks if missing
  const fallback = returnType === 'gstr1' ? GSTR1_FALLBACK : GSTR2A_FALLBACK;
  for (const [field, [r, c]] of Object.entries(fallback)) {
    if (!found[field] && rows[r] && rows[r][c]) {
      const val = cleanStr(rows[r][c]);
      if (val) found[field] = val;
    }
  }

  const gstin = cleanStr(found.gstin).toUpperCase();
  const legalName = cleanStr(found.legal_name);
  const tradeName = cleanStr(found.trade_name);
  const fyInfo = parseFinancialYear(found.financial_year);
  const financialYear = fyInfo.raw;

  const periodInfo =
    returnType === 'gstr1'
      ? parseGstr1TaxPeriod(found.tax_period, financialYear)
      : parseGstr2aTaxPeriod(found.tax_period, financialYear);

  return {
    dealer_id: gstin ? `dealer_${gstin}` : '',
    gstin,
    legal_name: legalName,
    trade_name: tradeName,
    financial_year: financialYear,
    tax_period: periodInfo.display || cleanStr(found.tax_period),
    tax_period_raw: periodInfo.raw,
    tax_period_month: periodInfo.month,
    tax_period_year: periodInfo.year,
    tax_period_display: periodInfo.display,
    // CamelCase aliases
    legalName,
    tradeName,
    financialYear,
    taxPeriod: periodInfo.display || cleanStr(found.tax_period),
    taxPeriodRaw: periodInfo.raw,
    taxPeriodMonth: periodInfo.month,
    taxPeriodYear: periodInfo.year,
    taxPeriodDisplay: periodInfo.display,
    // Other fields
    arn: cleanStr(found.arn),
    arn_date: cleanStr(found.arn_date),
    download_date: cleanStr(found.download_date),
  };
}

export async function extractDealerMetadataFromFile(file, returnType) {
  const wb = await readWorkbook(file);
  const readmeName = wb.SheetNames.find((name) => README_SHEET_NAMES.has(name.trim().toLowerCase()));
  if (!readmeName) {
    return {
      dealer_id: '',
      gstin: '',
      legal_name: '',
      trade_name: '',
      financial_year: '',
      tax_period: '',
      tax_period_raw: '',
      tax_period_month: null,
      tax_period_year: null,
      tax_period_display: '',
      legalName: '',
      tradeName: '',
      financialYear: '',
      taxPeriod: '',
      taxPeriodRaw: '',
      taxPeriodMonth: null,
      taxPeriodYear: null,
      taxPeriodDisplay: '',
      arn: '',
      arn_date: '',
      download_date: '',
    };
  }

  const sheet = wb.Sheets[readmeName];
  const rows = sheetTo2DArray(sheet);
  return extractDealerMetadataFromSheet(rows, returnType);
}

export async function extractDealerMetadataFromFiles(files, returnType) {
  const results = [];
  for (const file of files) {
    const dealer = await extractDealerMetadataFromFile(file, returnType);
    results.push({ filename: file.name, dealer });
  }

  // Validate consistency across files
  const first = results[0]?.dealer;
  const mismatches = [];

  if (first?.gstin) {
    for (const item of results) {
      if (item.dealer.gstin && item.dealer.gstin !== first.gstin) {
        mismatches.push({
          field: 'GSTIN',
          source_file: item.filename,
          expected: first.gstin,
          found: item.dealer.gstin,
        });
      }
    }
  }

  if (first?.financial_year) {
    for (const item of results) {
      if (item.dealer.financial_year && item.dealer.financial_year !== first.financial_year) {
        mismatches.push({
          field: 'Financial Year',
          source_file: item.filename,
          expected: first.financial_year,
          found: item.dealer.financial_year,
        });
      }
    }
  }

  if (mismatches.length > 0) {
    const err = new Error('Dealer metadata mismatch across files');
    err.payload = {
      error_type: 'dealer_mismatch',
      mismatches,
      message: mismatches
        .map(
          (m) =>
            `${m.field} mismatch in ${m.source_file}: expected "${m.expected}", found "${m.found}"`,
        )
        .join('; '),
    };
    throw err;
  }

  // Compute period range from all selected valid files
  const periodObjects = results.map((r) => ({
    month: r.dealer.tax_period_month,
    year: r.dealer.tax_period_year,
    display: r.dealer.tax_period_display,
    raw: r.dealer.tax_period_raw,
  }));
  const periodRangeDisplay = buildTaxPeriodRangeDisplay(periodObjects);

  const combinedDealer = {
    ...(first || {}),
    tax_period: periodRangeDisplay || first?.tax_period || '',
    taxPeriod: periodRangeDisplay || first?.taxPeriod || '',
  };

  return {
    dealer: combinedDealer,
    files_analyzed: results.length,
    file_metadata: results,
    workbook_id: `wb_${returnType}_${first?.gstin || 'unknown'}_${Date.now()}`,
    return_type: returnType,
    source_files: files.map((f) => f.name),
  };
}
