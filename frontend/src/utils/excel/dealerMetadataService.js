import { readWorkbook, sheetTo2DArray, cleanStr } from './excelUtils';

const README_SHEET_NAMES = new Set(['read me', 'readme']);

const FIELD_ALIASES = {
  gstin: ['gstin', "taxpayer's gstin", 'taxpayers gstin'],
  legal_name: ['legal name', 'legal name of taxpayer'],
  trade_name: ['trade name', 'trade name (if any)'],
  financial_year: ['financial year'],
  tax_period: ['tax period', 'tax period '],
  arn: ['arn'],
  arn_date: ['arn date'],
  download_date: [
    'date and time of generation',
    'date of generation',
    'download date',
    'date of download',
  ],
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

function normalizeLabel(text) {
  if (text == null) return '';
  return String(text).trim().toLowerCase().replace(/\s+/g, ' ');
}

function matchField(label) {
  const normalized = normalizeLabel(label);
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

export function extractDealerMetadataFromSheet(rows, returnType) {
  const found = {};
  const maxRows = Math.min(rows.length, 25);

  for (let r = 0; r < maxRows; r++) {
    const row = rows[r] || [];
    const maxCols = Math.min(row.length, 10);
    for (let c = 0; c < maxCols; c++) {
      const cellVal = row[c];
      const field = matchField(cellVal);
      if (!field || found[field]) continue;

      // Scan right for value
      for (let vc = c + 1; vc < maxCols; vc++) {
        const val = cleanStr(row[vc]);
        if (!val) continue;
        if (matchField(val)) break;
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

  return {
    dealer_id: found.gstin ? `dealer_${found.gstin}` : '',
    gstin: found.gstin || '',
    legal_name: found.legal_name || '',
    trade_name: found.trade_name || '',
    financial_year: found.financial_year || '',
    tax_period: found.tax_period || '',
    arn: found.arn || '',
    arn_date: found.arn_date || '',
    download_date: found.download_date || '',
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

  if (mismatches.length > 0) {
    const err = new Error('Dealer metadata mismatch across files');
    err.payload = {
      error_type: 'dealer_mismatch',
      mismatches,
      message: mismatches.map((m) => `${m.field} mismatch in ${m.source_file}: expected "${m.expected}", found "${m.found}"`).join('; '),
    };
    throw err;
  }

  return {
    dealer: first || {},
    files_analyzed: results.length,
    workbook_id: `wb_${returnType}_${first?.gstin || 'unknown'}_${Date.now()}`,
    return_type: returnType,
    source_files: files.map((f) => f.name),
  };
}
