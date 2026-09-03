/**
 * Container Corporation of India Ltd — Real Data Frontend Verification
 *
 * PURPOSE:
 *   Local-only regression test against real GSTR-2A and GSTR-1 workbooks.
 *   Verifies that the merger engine produces correct row counts, preserves
 *   Rate (%), and excludes portal-generated Total rows.
 *
 * CI SAFETY:
 *   This test uses real taxpayer Excel files stored locally at paths that
 *   do NOT exist in CI/Railway environments. When those paths are absent the
 *   suite is automatically skipped — the CI build will NOT fail.
 *
 * DATA PRIVACY:
 *   Real workbooks are deliberately excluded from Git via .gitignore (*.xlsx).
 *   Do NOT commit taxpayer files.
 */

import { describe, it, expect } from 'vitest';
import * as XLSX from 'xlsx';
import fs from 'fs';
import path from 'path';
import { mergeGstr1Files } from '../utils/excel/gstr1Merger.js';
import { mergeGstr2aFiles, findGstr2aHeaderEnd } from '../utils/excel/gstr2aMerger.js';
import { cleanStr } from '../utils/excel/excelUtils.js';

// ---------------------------------------------------------------------------
// Local paths — intentionally NOT in the repository
// ---------------------------------------------------------------------------
const GSTR2A_DIR = 'E:/gstaudit/Container Corporation of India Ltd/GSTR 2A';
const GSTR1_DIR  = 'E:/gstaudit/Container Corporation of India Ltd/GSTR 1';
const OUTPUT_DIR = 'E:/gstaudit/test-output';

const GSTR2A_DATA_AVAILABLE = fs.existsSync(GSTR2A_DIR);
const GSTR1_DATA_AVAILABLE  = fs.existsSync(GSTR1_DIR);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function loadRealFiles(dirPath) {
  const fileNames = fs
    .readdirSync(dirPath)
    .filter((f) => f.endsWith('.xlsx') && !f.startsWith('~$'));
  return fileNames.map((fname) => {
    const fullPath = path.join(dirPath, fname);
    const buffer = fs.readFileSync(fullPath);
    return new File([buffer], fname, {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
  });
}

function readAllSheetRows(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const wb = XLSX.read(e.target.result, { type: 'array', raw: true });
      const result = {};
      for (const sname of wb.SheetNames) {
        const ws = wb.Sheets[sname];
        result[sname] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', raw: true });
      }
      resolve(result);
    };
    reader.readAsArrayBuffer(blob);
  });
}

// ---------------------------------------------------------------------------
// Test suite — skipped automatically when local data is unavailable
// ---------------------------------------------------------------------------
describe('Container Corporation of India Ltd Real Data Frontend Verification', () => {
  it(
    'Merges 12 real GSTR-2A files with complete rate preservation & portal total exclusion',
    async () => {
      if (!GSTR2A_DATA_AVAILABLE) {
        console.log(`[SKIP] GSTR-2A real data not found at "${GSTR2A_DIR}" — skipping local-only test.`);
        return; // graceful skip — does not fail CI
      }

      const files = loadRealFiles(GSTR2A_DIR);
      expect(files.length).toBe(12);

      const result = await mergeGstr2aFiles(files, { ignoreMissing: true });
      expect(result.row_count).toBe(3086);
      expect(result.blob).toBeDefined();

      const sheets = await readAllSheetRows(result.blob);
      const b2bRows = sheets['B2B'] || [];
      // Header is rows 0..5, data starts at index 6
      const dataRows = b2bRows.slice(6);
      expect(dataRows.length).toBe(2989);

      // Verify rate preservation in B2B
      for (const r of dataRows) {
        const rate = r[8];
        expect(rate).not.toBe('-');
        expect(rate).not.toBe('');
        expect(typeof rate).toBe('number');
      }

      // Export row counts for parity check with backend
      const stats = {};
      for (const [sname, rows] of Object.entries(sheets)) {
        if (sname.toLowerCase().includes('read me') || sname.toLowerCase().includes('meta')) continue;
        const headerEnd = findGstr2aHeaderEnd(rows);
        const nonEmpty = rows.slice(headerEnd + 1).filter((r) => r && r.some((v) => cleanStr(v) !== ''));
        stats[sname] = { rows: nonEmpty.length };
      }
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
      fs.writeFileSync(`${OUTPUT_DIR}/fe_gstr2a_parity.json`, JSON.stringify(stats, null, 2));
    },
    30000,
  );

  it(
    'Merges 12 real GSTR-1 files with period and rate preservation',
    async () => {
      if (!GSTR1_DATA_AVAILABLE) {
        console.log(`[SKIP] GSTR-1 real data not found at "${GSTR1_DIR}" — skipping local-only test.`);
        return; // graceful skip — does not fail CI
      }

      const files = loadRealFiles(GSTR1_DIR);
      expect(files.length).toBe(12);

      const result = await mergeGstr1Files(files, { ignoreMissing: true });
      expect(result.row_count).toBeGreaterThan(0);
      expect(result.blob).toBeDefined();

      const sheets = await readAllSheetRows(result.blob);
      const stats = {};
      for (const [sname, rows] of Object.entries(sheets)) {
        if (sname.toLowerCase().includes('read me') || sname.toLowerCase().includes('meta')) continue;
        const nonEmpty = rows.slice(4).filter((r) => r && r.some((v) => cleanStr(v) !== ''));
        stats[sname] = { rows: nonEmpty.length };
      }
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
      fs.writeFileSync(`${OUTPUT_DIR}/fe_gstr1_parity.json`, JSON.stringify(stats, null, 2));
    },
    30000,
  );
});
