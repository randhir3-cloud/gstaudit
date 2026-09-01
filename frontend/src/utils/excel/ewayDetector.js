import { readWorkbookRaw, sheetTo2DArray, cleanStr, MONTH_MAP } from './excelUtils.js';
import { normalizeGSTIN, isValidGSTIN } from '../formatGSTIN.js';

const ROWS_TO_INSPECT = 500;
const DOMINANCE_THRESHOLD = 0.70; // 70% dominance threshold for direction

const FROM_GSTIN_ALIASES = [
  'from gstin',
  'from gstin and name',
  'from gstin and trade name',
  'from gstin/name',
  'consigner gstin',
  'consignor gstin',
  'supplier gstin',
  'seller gstin',
  'dispatch gstin',
];

const TO_GSTIN_ALIASES = [
  'to gstin',
  'to gstin and name',
  'to gstin and trade name',
  'to gstin/name',
  'consignee gstin',
  'recipient gstin',
  'buyer gstin',
  'receiver gstin',
];

const EWB_DATE_ALIASES = [
  'ewb no and dt',
  'ewb no. and dt.',
  'ewb date',
  'eway date',
  'doc no and dt',
  'doc no. and dt.',
  'doc date',
  'document date',
  'invoice date',
  'date',
  'ewb no',
  'ewb number',
];

const DOC_NO_ALIASES = [
  'doc no',
  'doc no and dt',
  'doc no. and dt.',
  'doc no.',
  'document no',
  'invoice no',
];

function normalizeColName(val) {
  if (val == null) return '';
  return String(val)
    .trim()
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[.\-_/]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function findGstinInVal(val) {
  if (val == null) return '';
  const text = String(val).trim().toUpperCase();
  const direct = normalizeGSTIN(text);
  if (isValidGSTIN(direct)) return direct;
  const match = text.match(/\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b/);
  return match ? match[1] : '';
}

export function extractPartyNameFromCell(cellVal, dealerGstin) {
  if (!cellVal) return '';
  const str = String(cellVal).trim();
  if (str.includes('/')) {
    const parts = str.split('/');
    for (let part of parts) {
      part = part.trim();
      if (dealerGstin && part.toUpperCase().includes(dealerGstin)) continue;
      // Remove noise like leading "s. " or punctuation
      const cleaned = part.replace(/^[sS]\.\s*/, '').replace(/^[,.\s]+|[,.\s]+$/g, '').trim();
      if (cleaned.length >= 3 && !/^[0-9]+$/.test(cleaned)) {
        return cleaned;
      }
    }
  }
  return '';
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

export function parsePeriodFromEwayDate(val) {
  if (val == null) return { month: '', financial_year: '' };
  const text = cleanStr(val);
  if (!text) return { month: '', financial_year: '' };

  const datePart = text.includes(' - ') ? text.split(' - ')[1].trim() : text;
  const dateStr = datePart.includes(' ') ? datePart.split(' ')[0] : datePart;

  const m = dateStr.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})$/);
  if (m) {
    const mm = String(m[2]).padStart(2, '0');
    const yyyyInt = parseInt(m[3].length === 2 ? `20${m[3]}` : m[3], 10);
    const mmInt = parseInt(mm, 10);
    const month = `${MONTH_MAP[mm] || mm} ${yyyyInt}`;
    const fyStart = mmInt >= 4 ? yyyyInt : yyyyInt - 1;
    const fyEnd = (fyStart + 1) % 100;
    const financial_year = `${fyStart}-${String(fyEnd).padStart(2, '0')}`;
    return { month, financial_year };
  }
  return { month: '', financial_year: '' };
}

/** Extract clean data rows and columns from worksheet rows */
export function parseEwaySheetRows(rawRows) {
  if (!rawRows || rawRows.length === 0) {
    return { headerRowIdx: -1, headers: [], fromColIdx: -1, toColIdx: -1, ewbDateColIdx: -1, dataRows: [] };
  }

  let headerRowIdx = -1;
  let fromColIdx = -1;
  let toColIdx = -1;
  let ewbDateColIdx = -1;

  for (let r = 0; r < Math.min(rawRows.length, 10); r++) {
    const row = rawRows[r] || [];
    const fIdx = matchColIndex(row, FROM_GSTIN_ALIASES);
    const tIdx = matchColIndex(row, TO_GSTIN_ALIASES);
    if (fIdx !== -1 || tIdx !== -1) {
      headerRowIdx = r;
      fromColIdx = fIdx;
      toColIdx = tIdx;
      ewbDateColIdx = matchColIndex(row, EWB_DATE_ALIASES);
      break;
    }
  }

  if (headerRowIdx === -1) {
    return { headerRowIdx: -1, headers: [], fromColIdx: -1, toColIdx: -1, ewbDateColIdx: -1, dataRows: [] };
  }

  const headers = rawRows[headerRowIdx] || [];
  const rawData = rawRows.slice(headerRowIdx + 1);

  // Filter out blank rows or duplicate header rows
  const dataRows = rawData.filter((row) => {
    if (!row || !row.some((val) => cleanStr(val) !== '')) return false;
    // Exclude repeated header rows if any
    const firstCell = normalizeColName(row[0]);
    if (firstCell === 'ewb no' || firstCell === 'ewb no.') return false;
    return true;
  });

  return { headerRowIdx, headers, fromColIdx, toColIdx, ewbDateColIdx, dataRows };
}

/** Resolve single dealer GSTIN, legal name, and FY across all uploaded files */
export function resolveBatchDealerGstin(parsedFiles, preferredGstin = '') {
  if (preferredGstin && isValidGSTIN(normalizeGSTIN(preferredGstin))) {
    return { gstin: normalizeGSTIN(preferredGstin), source: 'context', legal_name: '', financial_year: '' };
  }

  const allToGstins = {};
  const allFromGstins = {};
  const namesByGstin = {};
  const fySet = new Set();
  const monthsSet = new Set();
  let totalRows = 0;

  for (const { dataRows, fromColIdx, toColIdx, ewbDateColIdx } of parsedFiles) {
    totalRows += dataRows.length;
    for (const row of dataRows) {
      const fG = fromColIdx !== -1 ? findGstinInVal(row[fromColIdx]) : '';
      const tG = toColIdx !== -1 ? findGstinInVal(row[toColIdx]) : '';
      if (fG) {
        allFromGstins[fG] = (allFromGstins[fG] || 0) + 1;
        const name = extractPartyNameFromCell(row[fromColIdx], fG);
        if (name) {
          if (!namesByGstin[fG]) namesByGstin[fG] = {};
          namesByGstin[fG][name] = (namesByGstin[fG][name] || 0) + 1;
        }
      }
      if (tG) {
        allToGstins[tG] = (allToGstins[tG] || 0) + 1;
        const name = extractPartyNameFromCell(row[toColIdx], tG);
        if (name) {
          if (!namesByGstin[tG]) namesByGstin[tG] = {};
          namesByGstin[tG][name] = (namesByGstin[tG][name] || 0) + 1;
        }
      }

      if (ewbDateColIdx !== -1 && row[ewbDateColIdx]) {
        const periodObj = parsePeriodFromEwayDate(row[ewbDateColIdx]);
        if (periodObj.financial_year) fySet.add(periodObj.financial_year);
        if (periodObj.month) monthsSet.add(periodObj.month);
      }
    }
  }

  if (totalRows === 0) {
    return { gstin: '', source: 'none', legal_name: '', financial_year: '' };
  }

  // Check top To GSTIN frequency
  let topToGstin = '';
  let topToCount = 0;
  for (const [g, count] of Object.entries(allToGstins)) {
    if (count > topToCount) {
      topToCount = count;
      topToGstin = g;
    }
  }

  // Check top From GSTIN frequency
  let topFromGstin = '';
  let topFromCount = 0;
  for (const [g, count] of Object.entries(allFromGstins)) {
    if (count > topFromCount) {
      topFromCount = count;
      topFromGstin = g;
    }
  }

  let resolvedGstin = '';
  let resolvedSource = 'none';

  // Inward batch: One dominant recipient GSTIN in To column across files
  if (topToGstin && topToCount / totalRows >= 0.50 && topToCount >= topFromCount) {
    resolvedGstin = topToGstin;
    resolvedSource = 'inward_batch';
  } else if (topFromGstin && topFromCount / totalRows >= 0.50) {
    // Outward batch: One dominant supplier GSTIN in From column across files
    resolvedGstin = topFromGstin;
    resolvedSource = 'outward_batch';
  } else if (topToCount > topFromCount) {
    resolvedGstin = topToGstin;
    resolvedSource = 'to_dominant';
  } else if (topFromCount > 0) {
    resolvedGstin = topFromGstin;
    resolvedSource = 'from_dominant';
  }

  // Extract dominant legal name for resolved GSTIN
  let resolvedLegalName = '';
  if (resolvedGstin && namesByGstin[resolvedGstin]) {
    let topNameCount = 0;
    for (const [name, count] of Object.entries(namesByGstin[resolvedGstin])) {
      if (count > topNameCount) {
        topNameCount = count;
        resolvedLegalName = name;
      }
    }
  }

  // Extract resolved FY
  let resolvedFy = '';
  const fys = Array.from(fySet);
  if (fys.length === 1) {
    resolvedFy = fys[0];
  } else if (fys.length > 1) {
    resolvedFy = fys.sort().join(', ');
  }

  return {
    gstin: resolvedGstin,
    source: resolvedSource,
    legal_name: resolvedLegalName,
    financial_year: resolvedFy,
    total_rows: totalRows,
    unique_months_count: monthsSet.size,
  };
}

/** Detect direction of a single parsed file */
export function classifySingleParsedFile(fileData, dealerGstin, expectedDirection = null) {
  const { filename, dataRows, fromColIdx, toColIdx, ewbDateColIdx, headers } = fileData;

  if (fromColIdx === -1 && toColIdx === -1) {
    return {
      filename,
      detected_type: 'unknown',
      confidence: 0,
      dealer_gstin: dealerGstin || '',
      month: '',
      financial_year: '',
      status: 'unknown',
      message: 'Could not find From GSTIN or To GSTIN columns in workbook.',
      rows_inspected: 0,
    };
  }

  if (dataRows.length === 0) {
    return {
      filename,
      detected_type: 'unknown',
      confidence: 0,
      dealer_gstin: dealerGstin || '',
      month: '',
      financial_year: '',
      status: 'unknown',
      message: 'No data rows found in workbook.',
      rows_inspected: 0,
    };
  }

  // Extract period and FY from first data row's date or filename
  let month = '';
  let financial_year = '';
  if (ewbDateColIdx !== -1 && dataRows[0]?.[ewbDateColIdx]) {
    const periodObj = parsePeriodFromEwayDate(dataRows[0][ewbDateColIdx]);
    month = periodObj.month;
    financial_year = periodObj.financial_year;
  }

  if (!month) {
    const periodMatch = filename.match(/_(\d{2})(\d{4})_/);
    if (periodMatch) {
      month = `${periodMatch[1]}/${periodMatch[2]}`;
      const mm = parseInt(periodMatch[1], 10);
      const yy = parseInt(periodMatch[2], 10);
      const startYr = mm >= 4 ? yy : yy - 1;
      financial_year = `${startYr}-${String((startYr + 1) % 100).padStart(2, '0')}`;
    }
  }

  const dealer = normalizeGSTIN(dealerGstin);

  let fromMatches = 0;
  let toMatches = 0;
  const inspectedRows = Math.min(dataRows.length, ROWS_TO_INSPECT);

  for (let i = 0; i < inspectedRows; i++) {
    const row = dataRows[i];
    const fG = fromColIdx !== -1 ? findGstinInVal(row[fromColIdx]) : '';
    const tG = toColIdx !== -1 ? findGstinInVal(row[toColIdx]) : '';
    if (dealer) {
      if (fG === dealer) fromMatches++;
      if (tG === dealer) toMatches++;
    }
  }

  const fromRate = inspectedRows > 0 ? fromMatches / inspectedRows : 0;
  const toRate = inspectedRows > 0 ? toMatches / inspectedRows : 0;

  let detectedType = 'unknown';
  let confidence = 0;
  let message = '';

  if (dealer) {
    if (toRate >= DOMINANCE_THRESHOLD && toRate > fromRate) {
      detectedType = 'inward';
      confidence = Math.round(toRate * 100);
      message = `Dealer GSTIN (${dealer}) in To GSTIN (${confidence}% of ${inspectedRows} rows).`;
    } else if (fromRate >= DOMINANCE_THRESHOLD && fromRate > toRate) {
      detectedType = 'outward';
      confidence = Math.round(fromRate * 100);
      message = `Dealer GSTIN (${dealer}) in From GSTIN (${confidence}% of ${inspectedRows} rows).`;
    } else if (fromRate > 0 && toRate > 0) {
      detectedType = 'unknown';
      confidence = Math.round(Math.max(fromRate, toRate) * 100);
      message = `Mixed occurrences of Dealer GSTIN: ${Math.round(fromRate * 100)}% From vs ${Math.round(toRate * 100)}% To.`;
    } else {
      detectedType = 'unknown';
      confidence = Math.round(Math.max(fromRate, toRate) * 100);
      message = `Dealer GSTIN ${dealer} not found in From (${Math.round(fromRate * 100)}%) or To (${Math.round(toRate * 100)}%) across ${inspectedRows} rows.`;
    }
  } else {
    // If no dealer could be resolved at all
    detectedType = 'unknown';
    confidence = 0;
    message = 'Dealer GSTIN could not be identified automatically.';
  }

  let status = 'valid';
  if (detectedType === 'unknown') {
    status = dealer ? 'unknown' : 'pending_dealer_gstin';
  } else if (expectedDirection && detectedType !== expectedDirection) {
    status = 'wrong_section';
  }

  return {
    filename,
    detected_type: detectedType,
    confidence,
    dealer_gstin: dealer || '',
    month,
    financial_year,
    status,
    message,
    rows_inspected: dataRows.length,
    from_matches: fromMatches,
    to_matches: toMatches,
    from_rate: Math.round(fromRate * 100),
    to_rate: Math.round(toRate * 100),
  };
}

/** Classify a single file object */
export async function classifyEwayFile(file, dealerGstin = '', expectedDirection = null) {
  const wb = await readWorkbookRaw(file);
  let allRows = [];
  for (const name of wb.SheetNames) {
    const rows = sheetTo2DArray(wb.Sheets[name]);
    if (rows.length > 0) {
      allRows = allRows.concat(rows);
    }
  }

  const parsed = parseEwaySheetRows(allRows);
  const fileData = {
    filename: file.name,
    ...parsed,
  };

  const resolvedDealer = dealerGstin || resolveBatchDealerGstin([fileData]).gstin;
  return classifySingleParsedFile(fileData, resolvedDealer, expectedDirection);
}

/** Classify a collection of files with intelligent cross-file dealer resolution */
export async function classifyEwayFiles(files, options = {}) {
  const parsedFiles = [];

  for (const file of files) {
    const wb = await readWorkbookRaw(file);
    let allRows = [];
    for (const name of wb.SheetNames) {
      const rows = sheetTo2DArray(wb.Sheets[name]);
      if (rows.length > 0) {
        allRows = allRows.concat(rows);
      }
    }
    const parsed = parseEwaySheetRows(allRows);
    parsedFiles.push({
      filename: file.name,
      ...parsed,
    });
  }

  // Cross-file resolution of Dealer GSTIN
  const batchResolution = resolveBatchDealerGstin(parsedFiles, options.dealerGstin);
  const effectiveDealer = batchResolution.gstin;

  const classifications = parsedFiles.map((fData) => {
    return classifySingleParsedFile(fData, effectiveDealer, options.expectedDirection);
  });

  return {
    classifications,
    dealer_resolution: {
      gstin: effectiveDealer,
      source: batchResolution.source,
      legal_name: batchResolution.legal_name || '',
      financial_year: batchResolution.financial_year || '',
      total_rows: batchResolution.total_rows || 0,
      unique_months_count: batchResolution.unique_months_count || 0,
      requires_user_input: !effectiveDealer,
    },
    total_files: files.length,
    valid_count: classifications.filter((c) => c.status === 'valid').length,
    wrong_section_count: classifications.filter((c) => c.status === 'wrong_section').length,
    unknown_count: classifications.filter((c) => c.status === 'unknown' || c.status === 'pending_dealer_gstin').length,
  };
}
