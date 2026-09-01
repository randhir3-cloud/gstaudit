import { readWorkbookRaw, sheetTo2DArray, cleanStr, GSTIN_REGEX } from './excelUtils';

const ROWS_TO_INSPECT = 100;
const MATCH_THRESHOLD = 0.8;

const FROM_GSTIN_ALIASES = [
  'from gstin',
  'from gstin & name',
  'from gstin and name',
  'from gstin/name',
  'consigner gstin',
  'consignor gstin',
  'supplier gstin',
  'seller gstin',
  'dispatch gstin',
];

const TO_GSTIN_ALIASES = [
  'to gstin',
  'to gstin & name',
  'to gstin and name',
  'to gstin/name',
  'consignee gstin',
  'recipient gstin',
  'buyer gstin',
  'receiver gstin',
];

function normalizeColName(val) {
  if (val == null) return '';
  return String(val)
    .trim()
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/\s+/g, ' ');
}

function findGstinInVal(val) {
  if (val == null) return '';
  const text = String(val).trim().toUpperCase();
  if (GSTIN_REGEX.test(text)) return text;
  const match = text.match(/\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b/);
  return match ? match[1] : '';
}

function matchColIndex(headers, aliases) {
  for (let i = 0; i < headers.length; i++) {
    const norm = normalizeColName(headers[i]);
    for (const alias of aliases) {
      if (norm === alias) return i;
    }
  }
  for (let i = 0; i < headers.length; i++) {
    const norm = normalizeColName(headers[i]);
    for (const alias of aliases) {
      if (norm.includes(alias) || alias.includes(norm)) return i;
    }
  }
  return -1;
}

export function detectEwayDirectionFromRows(rows, dealerGstin) {
  if (!rows || rows.length === 0) {
    return {
      detectedType: 'unknown',
      confidence: 0,
      status: 'unknown',
      message: 'No rows in workbook',
    };
  }

  // Find header row (usually row 0 or 1)
  let headerRowIdx = -1;
  let fromColIdx = -1;
  let toColIdx = -1;

  for (let r = 0; r < Math.min(rows.length, 5); r++) {
    const row = rows[r] || [];
    const fromIdx = matchColIndex(row, FROM_GSTIN_ALIASES);
    const toIdx = matchColIndex(row, TO_GSTIN_ALIASES);
    if (fromIdx !== -1 || toIdx !== -1) {
      headerRowIdx = r;
      fromColIdx = fromIdx;
      toColIdx = toIdx;
      break;
    }
  }

  if (headerRowIdx === -1) {
    return {
      detectedType: 'unknown',
      confidence: 0,
      status: 'unknown',
      message: 'Could not find From/To GSTIN columns in header',
    };
  }

  const dealer = cleanStr(dealerGstin).toUpperCase();

  // If no dealer GSTIN provided, attempt to infer it from frequent GSTIN in From or To
  const dataRows = rows.slice(headerRowIdx + 1, headerRowIdx + 1 + ROWS_TO_INSPECT);
  if (dataRows.length === 0) {
    return {
      detectedType: 'unknown',
      confidence: 0,
      status: 'unknown',
      message: 'No data rows found',
    };
  }

  let effectiveDealer = dealer;
  if (!effectiveDealer) {
    // Count frequencies of GSTINs in fromCol and toCol
    const fromCounts = {};
    const toCounts = {};
    for (const row of dataRows) {
      if (fromColIdx !== -1) {
        const g = findGstinInVal(row[fromColIdx]);
        if (g) fromCounts[g] = (fromCounts[g] || 0) + 1;
      }
      if (toColIdx !== -1) {
        const g = findGstinInVal(row[toColIdx]);
        if (g) toCounts[g] = (toCounts[g] || 0) + 1;
      }
    }

    // Find if From GSTIN has a single dominant GSTIN (>80%)
    let topFromGstin = '';
    let topFromCount = 0;
    for (const [g, count] of Object.entries(fromCounts)) {
      if (count > topFromCount) {
        topFromCount = count;
        topFromGstin = g;
      }
    }

    let topToGstin = '';
    let topToCount = 0;
    for (const [g, count] of Object.entries(toCounts)) {
      if (count > topToCount) {
        topToCount = count;
        topToGstin = g;
      }
    }

    if (topFromCount / dataRows.length >= MATCH_THRESHOLD) {
      return {
        detectedType: 'outward',
        confidence: 100,
        status: 'valid',
        dealerGstin: topFromGstin,
        fromCol: rows[headerRowIdx][fromColIdx],
        toCol: toColIdx !== -1 ? rows[headerRowIdx][toColIdx] : '',
        message: 'Dominant GSTIN in From GSTIN column (Outward).',
      };
    }

    if (topToCount / dataRows.length >= MATCH_THRESHOLD) {
      return {
        detectedType: 'inward',
        confidence: 100,
        status: 'valid',
        dealerGstin: topToGstin,
        fromCol: fromColIdx !== -1 ? rows[headerRowIdx][fromColIdx] : '',
        toCol: rows[headerRowIdx][toColIdx],
        message: 'Dominant GSTIN in To GSTIN column (Inward).',
      };
    }

    return {
      detectedType: 'unknown',
      confidence: 0,
      status: 'pending_dealer_gstin',
      message: 'Dealer GSTIN is required for classification.',
    };
  }

  // If dealer GSTIN is known, check match rates
  let fromMatches = 0;
  let toMatches = 0;
  let count = 0;

  for (const row of dataRows) {
    count++;
    if (fromColIdx !== -1) {
      const g = findGstinInVal(row[fromColIdx]);
      if (g === effectiveDealer) fromMatches++;
    }
    if (toColIdx !== -1) {
      const g = findGstinInVal(row[toColIdx]);
      if (g === effectiveDealer) toMatches++;
    }
  }

  const fromRate = count > 0 ? fromMatches / count : 0;
  const toRate = count > 0 ? toMatches / count : 0;

  const fromMatch = fromRate >= MATCH_THRESHOLD;
  const toMatch = toRate >= MATCH_THRESHOLD;

  if (fromMatch && toMatch) {
    return {
      detectedType: 'unknown',
      confidence: 0,
      status: 'unknown',
      dealerGstin: effectiveDealer,
      message: 'Dealer GSTIN appears in both From and To columns.',
    };
  }

  if (fromMatch) {
    return {
      detectedType: 'outward',
      confidence: Math.round(fromRate * 100),
      status: 'valid',
      dealerGstin: effectiveDealer,
      fromCol: rows[headerRowIdx][fromColIdx],
      toCol: toColIdx !== -1 ? rows[headerRowIdx][toColIdx] : '',
      message: 'Dealer GSTIN predominantly in From GSTIN column.',
    };
  }

  if (toMatch) {
    return {
      detectedType: 'inward',
      confidence: Math.round(toRate * 100),
      status: 'valid',
      dealerGstin: effectiveDealer,
      fromCol: fromColIdx !== -1 ? rows[headerRowIdx][fromColIdx] : '',
      toCol: rows[headerRowIdx][toColIdx],
      message: 'Dealer GSTIN predominantly in To GSTIN column.',
    };
  }

  return {
    detectedType: 'unknown',
    confidence: Math.round(Math.max(fromRate, toRate) * 100),
    status: 'unknown',
    dealerGstin: effectiveDealer,
    message: 'Could not classify with 80% confidence.',
  };
}

export async function classifyEwayFile(file, dealerGstin = '', expectedDirection = null) {
  const wb = await readWorkbookRaw(file);
  let allRows = [];
  for (const name of wb.SheetNames) {
    const rows = sheetTo2DArray(wb.Sheets[name]);
    if (rows.length > 0) {
      allRows = allRows.concat(rows);
    }
  }

  const result = detectEwayDirectionFromRows(allRows, dealerGstin);

  let status = result.status;
  if (expectedDirection && result.detectedType !== 'unknown' && result.detectedType !== expectedDirection) {
    status = 'wrong_section';
  }

  const periodMatch = file.name.match(/_(\d{2})(\d{4})_/);
  const month = periodMatch ? `${periodMatch[1]}/${periodMatch[2]}` : '';
  let fy = '';
  if (periodMatch) {
    const mm = parseInt(periodMatch[1], 10);
    const yy = parseInt(periodMatch[2], 10);
    const startYr = mm >= 4 ? yy : yy - 1;
    fy = `${startYr}-${String((startYr + 1) % 100).padStart(2, '0')}`;
  }

  return {
    filename: file.name,
    detected_type: result.detectedType,
    confidence: result.confidence,
    dealer_gstin: result.dealerGstin || dealerGstin,
    month,
    financial_year: fy,
    status,
    message: result.message,
    rows_inspected: allRows.length,
  };
}

export async function classifyEwayFiles(files, options = {}) {
  const classifications = [];
  let resolvedDealer = options.dealerGstin || '';

  for (const file of files) {
    const res = await classifyEwayFile(file, resolvedDealer, options.expectedDirection);
    if (!resolvedDealer && res.dealer_gstin) {
      resolvedDealer = res.dealer_gstin;
    }
    classifications.push(res);
  }

  return {
    classifications,
    dealer_resolution: {
      gstin: resolvedDealer,
      source: resolvedDealer ? (options.dealerGstin ? 'user' : 'file') : 'none',
      requires_user_input: !resolvedDealer,
    },
    total_files: files.length,
    valid_count: classifications.filter((c) => c.status === 'valid').length,
    wrong_section_count: classifications.filter((c) => c.status === 'wrong_section').length,
    unknown_count: classifications.filter((c) => c.status === 'unknown' || c.status === 'pending_dealer_gstin').length,
  };
}
