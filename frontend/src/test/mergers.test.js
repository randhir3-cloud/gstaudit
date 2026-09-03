import { describe, it, expect } from 'vitest';
import * as XLSX from 'xlsx';
import { mergeGstr1Files } from '../utils/excel/gstr1Merger.js';
import { mergeGstr2aFiles } from '../utils/excel/gstr2aMerger.js';
import { normalizeRate, formatCleanRate, normalizeNumeric, isPortalTotalRow } from '../utils/excel/excelUtils.js';

function createGstr2aTestFile(filename, period, b2bRows, gstin = '03AABCV6919K1Z5') {
  const wb = XLSX.utils.book_new();

  // Read me sheet
  const readmeRows = [
    ['', '', '', '', ''],
    ['', '', gstin, '', period],
    ['', '', 'Test Dealer Ltd', '', '2022-23'],
    ['', '', 'Test Dealer', '', '11/05/2022'],
  ];
  const readmeWs = XLSX.utils.aoa_to_sheet(readmeRows);
  XLSX.utils.book_append_sheet(wb, readmeWs, 'Read me');

  // Header rows (rows 1-6)
  const allB2b = [
    ['Goods and Services Tax  - GSTR 2A', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['Taxable inward supplies received from registered persons', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['GSTIN of supplier', 'Trade/Legal name of the Supplier', 'Invoice details', '', '', '', 'Place of supply', 'Supply Attract Reverse Charge', 'Rate (%)', 'Taxable Value (₹)', 'Tax Amount', '', '', '', 'GSTR-1/IFF/GSTR-1A/5 Filing Status'],
    ['', '', 'Invoice number', 'Invoice type', 'Invoice Date', 'Invoice Value (₹)', '', '', '', '', 'Integrated Tax  (₹)', 'Central Tax (₹)', 'State/UT tax (₹)', 'Cess  (₹)', ''],
    ...b2bRows,
  ];

  const b2bWs = XLSX.utils.aoa_to_sheet(allB2b);
  XLSX.utils.book_append_sheet(wb, b2bWs, 'B2B');

  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new File([buf], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

function readOutputSheetRows(blob, sheetName) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const wb = XLSX.read(e.target.result, { type: 'array', raw: true });
      const ws = wb.Sheets[sheetName];
      const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', raw: true });
      resolve(rows);
    };
    reader.readAsArrayBuffer(blob);
  });
}

describe('GSTR-2A & GSTR-1 Merging & Rate Preservation Suite', () => {
  it('TEST 1 & 4: Excludes portal -Total row, preserves Rate 18% and detail record', async () => {
    const b2bData = [
      ['03AAFCN6922Q1Z2', 'NAVBHARAT CONSOLIDATION PVT LTD', 'INLUD/0181/22-23', 'R', '12-01-2023', 12980, 'Punjab', 'N', 18, 11000, 0, 990, 990, 0, 'Y'],
      ['03AAFCN6922Q1Z2', 'NAVBHARAT CONSOLIDATION PVT LTD', 'INLUD/0181/22-23-Total', 'R', '12-01-2023', 12980, 'Punjab', 'N', '-', 11000, 0, 990, 990, 0, 'Y'],
    ];

    const file = createGstr2aTestFile('03AABCV6919K1Z5_012023_R2A.xlsx', '012023', b2bData);
    const result = await mergeGstr2aFiles([file]);

    expect(result.row_count).toBe(1);
    const rows = await readOutputSheetRows(result.blob, 'B2B');
    // Row 0-5 are headers (indices 0..5), data row is index 6
    const dataRow = rows[6];
    expect(dataRow[2]).toBe('INLUD/0181/22-23');
    expect(dataRow[8]).toBe(18); // Rate 18 preserved!
    expect(dataRow[9]).toBe(11000);
    expect(dataRow[11]).toBe(990);
    expect(dataRow[12]).toBe(990);
    expect(dataRow[15]).toBe('Jan-2023'); // Source_Period
  });

  it('TEST 2: Same invoice, multiple rows, same rate -> aggregated into one row with summed tax values', async () => {
    const b2bData = [
      ['03AABCT1234A1Z1', 'SUPPLIER A', 'INV-001', 'R', '05-04-2022', 35400, 'Punjab', 'N', 18, 10000, 0, 900, 900, 0, 'Y'],
      ['03AABCT1234A1Z1', 'SUPPLIER A', 'INV-001', 'R', '05-04-2022', 35400, 'Punjab', 'N', 18, 20000, 0, 1800, 1800, 0, 'Y'],
      ['03AABCT1234A1Z1', 'SUPPLIER A', 'INV-001-Total', 'R', '05-04-2022', 35400, 'Punjab', 'N', '-', 30000, 0, 2700, 2700, 0, 'Y'],
    ];

    const file = createGstr2aTestFile('03AABCV6919K1Z5_042022_R2A.xlsx', '042022', b2bData);
    const result = await mergeGstr2aFiles([file]);

    expect(result.row_count).toBe(1);
    const rows = await readOutputSheetRows(result.blob, 'B2B');
    const dataRow = rows[6];
    expect(dataRow[2]).toBe('INV-001');
    expect(dataRow[8]).toBe(18);
    expect(dataRow[9]).toBe(30000); // 10000 + 20000 = 30000
    expect(dataRow[11]).toBe(2700); // 900 + 1800 = 2700
    expect(dataRow[12]).toBe(2700);
    expect(dataRow[5]).toBe(35400); // Invoice value not multiplied
  });

  it('TEST 3: Multi-rate invoice (5% and 18%) -> produces 2 separate rate-wise records', async () => {
    const b2bData = [
      ['03AABCT1234A1Z1', 'SUPPLIER A', 'INV-MULTI', 'R', '10-04-2022', 45000, 'Punjab', 'N', 5, 10000, 0, 250, 250, 0, 'Y'],
      ['03AABCT1234A1Z1', 'SUPPLIER A', 'INV-MULTI', 'R', '10-04-2022', 45000, 'Punjab', 'N', 18, 25000, 0, 2250, 2250, 0, 'Y'],
      ['03AABCT1234A1Z1', 'SUPPLIER A', 'INV-MULTI-Total', 'R', '10-04-2022', 45000, 'Punjab', 'N', '-', 35000, 0, 2500, 2500, 0, 'Y'],
    ];

    const file = createGstr2aTestFile('03AABCV6919K1Z5_042022_R2A.xlsx', '042022', b2bData);
    const result = await mergeGstr2aFiles([file]);

    expect(result.row_count).toBe(2);
    const rows = await readOutputSheetRows(result.blob, 'B2B');
    const rate5Row = rows.find((r) => r[2] === 'INV-MULTI' && r[8] === 5);
    const rate18Row = rows.find((r) => r[2] === 'INV-MULTI' && r[8] === 18);

    expect(rate5Row).toBeDefined();
    expect(rate5Row[9]).toBe(10000);
    expect(rate5Row[11]).toBe(250);

    expect(rate18Row).toBeDefined();
    expect(rate18Row[9]).toBe(25000);
    expect(rate18Row[11]).toBe(2250);
  });

  it('TEST 5: Multiple suppliers using same invoice number remain separate', async () => {
    const b2bData = [
      ['03AABCT1111A1Z1', 'SUPPLIER ONE', 'INV-COMMON', 'R', '15-04-2022', 11800, 'Punjab', 'N', 18, 10000, 0, 900, 900, 0, 'Y'],
      ['03AABCT1111A1Z1', 'SUPPLIER ONE', 'INV-COMMON-Total', 'R', '15-04-2022', 11800, 'Punjab', 'N', '-', 10000, 0, 900, 900, 0, 'Y'],
      ['03AABCT2222B1Z2', 'SUPPLIER TWO', 'INV-COMMON', 'R', '15-04-2022', 11800, 'Punjab', 'N', 18, 10000, 0, 900, 900, 0, 'Y'],
      ['03AABCT2222B1Z2', 'SUPPLIER TWO', 'INV-COMMON-Total', 'R', '15-04-2022', 11800, 'Punjab', 'N', '-', 10000, 0, 900, 900, 0, 'Y'],
    ];

    const file = createGstr2aTestFile('03AABCV6919K1Z5_042022_R2A.xlsx', '042022', b2bData);
    const result = await mergeGstr2aFiles([file]);

    expect(result.row_count).toBe(2);
  });

  it('TEST 6: Same invoice/rate with different Place of Supply remains separate', async () => {
    const b2bData = [
      ['03AABCT1111A1Z1', 'SUPPLIER ONE', 'INV-POS', 'R', '15-04-2022', 11800, 'Punjab', 'N', 18, 10000, 0, 900, 900, 0, 'Y'],
      ['03AABCT1111A1Z1', 'SUPPLIER ONE', 'INV-POS', 'R', '15-04-2022', 11800, 'Haryana', 'N', 18, 10000, 1800, 0, 0, 0, 'Y'],
    ];

    const file = createGstr2aTestFile('03AABCV6919K1Z5_042022_R2A.xlsx', '042022', b2bData);
    const result = await mergeGstr2aFiles([file]);

    expect(result.row_count).toBe(2);
  });

  it('TEST 7: Rate normalization treats 18, 18.0 and "18%" identically', () => {
    expect(normalizeRate(18)).toBe(18);
    expect(normalizeRate(18.0)).toBe(18);
    expect(normalizeRate('18')).toBe(18);
    expect(normalizeRate('18%')).toBe(18);
    expect(normalizeRate('18.00%')).toBe(18);
  });

  it('TEST 8: Distinguishes Rate 0% from blank / "-"', () => {
    expect(normalizeRate(0)).toBe(0);
    expect(normalizeRate('0')).toBe(0);
    expect(normalizeRate('0%')).toBe(0);
    expect(normalizeRate('-')).toBeNull();
    expect(normalizeRate('')).toBeNull();
    expect(normalizeRate(null)).toBeNull();
    expect(normalizeRate('NA')).toBeNull();
  });

  it('TEST 9: Decimal numeric tax values maintain precision', () => {
    expect(normalizeNumeric('1,25,000.50')).toBe(125000.50);
    expect(normalizeNumeric('₹ 4,237.29')).toBe(4237.29);
    expect(normalizeNumeric(1234.567)).toBe(1234.567);
  });

  it('TEST 11: Cross-file duplicate re-upload does not double-count transactions', async () => {
    const b2bData = [
      ['03AAFCN6922Q1Z2', 'NAVBHARAT CONSOLIDATION PVT LTD', 'INV-DUP-1', 'R', '12-01-2023', 12980, 'Punjab', 'N', 18, 11000, 0, 990, 990, 0, 'Y'],
      ['03AAFCN6922Q1Z2', 'NAVBHARAT CONSOLIDATION PVT LTD', 'INV-DUP-1-Total', 'R', '12-01-2023', 12980, 'Punjab', 'N', '-', 11000, 0, 990, 990, 0, 'Y'],
    ];

    const file1 = createGstr2aTestFile('03AABCV6919K1Z5_012023_R2A_file1.xlsx', '012023', b2bData);
    const file2 = createGstr2aTestFile('03AABCV6919K1Z5_012023_R2A_file2.xlsx', '012023', b2bData);

    const result = await mergeGstr2aFiles([file1, file2], { ignoreMissing: true });
    expect(result.row_count).toBe(1);
    expect(result.duplicate_rows_skipped).toBe(1);
  });

  it('TEST 12: GSTR-1 Multi-rate invoice preserves 5% and 18% lines separately', async () => {
    const wb = XLSX.utils.book_new();

    const readmeRows = [
      ['Header', 'Value'],
      ['1', 'Instructions'],
      ['2', 'More info'],
      ['Financial Year', '2022-23'],
      ['Tax Period', '042022'],
      ['GSTIN of Taxpayer', '03AABCV6919K1Z5'],
      ['Legal Name of Taxpayer', 'Test Company Ltd'],
      ['Trade Name', 'Test Company'],
      ['ARN', 'AA030422000001Z'],
      ['Date of ARN', '11/05/2022'],
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(readmeRows), 'Read me');

    const b2bRows = [
      ['Summary of B2B'],
      ['Note: Test'],
      ['Details'],
      ['GSTIN/UIN of Recipient', 'Receiver Name', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Place Of Supply', 'Reverse Charge', 'Invoice Type', 'Rate', 'Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT Tax', 'Cess Amount'],
      ['03AABCT1234A1Z1', 'Customer A', 'INV-G1-01', '01/05/2022', 50000, 'Punjab', 'N', 'Regular', 5, 10000, 0, 250, 250, 0],
      ['03AABCT1234A1Z1', 'Customer A', 'INV-G1-01', '01/05/2022', 50000, 'Punjab', 'N', 'Regular', 18, 30000, 0, 2700, 2700, 0],
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(b2bRows), 'b2b');

    const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
    const file = new File([buf], 'GSTR1_03AABCV6919K1Z5_042022_Inv_1.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

    const result = await mergeGstr1Files([file]);
    expect(result.row_count).toBe(2);

    const rows = await readOutputSheetRows(result.blob, 'b2b');
    const rate5 = rows.find((r) => r[2] === 'INV-G1-01' && r[8] === 5);
    const rate18 = rows.find((r) => r[2] === 'INV-G1-01' && r[8] === 18);

    expect(rate5).toBeDefined();
    expect(rate5[9]).toBe(10000);
    expect(rate18).toBeDefined();
    expect(rate18[9]).toBe(30000);
  });

  it('TEST 13: GSTR-1 HSN and B2CS preserve monthly traceability with Source_Period', async () => {
    const wb = XLSX.utils.book_new();

    const readmeRows = [
      ['Header', 'Value'],
      ['Financial Year', '2022-23'],
      ['Tax Period', '042022'],
      ['GSTIN of Taxpayer', '03AABCV6919K1Z5'],
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(readmeRows), 'Read me');

    const b2csRows = [
      ['Goods and Services Tax - Form GSTR-1'],
      [''],
      ['7 - B2CS'],
      ['Place Of Supply', 'Rate', 'Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT Tax', 'Cess Amount'],
      ['Punjab', 18, 10000, 0, 900, 900, 0],
      ['Punjab', 18, 5000, 0, 450, 450, 0],
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(b2csRows), 'b2cs');

    const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
    const file = new File([buf], 'GSTR1_03AABCV6919K1Z5_042022_Inv_1.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

    const result = await mergeGstr1Files([file]);
    expect(result.row_count).toBe(1); // Consolidates same POS + Rate within month into 1 row
    const rows = await readOutputSheetRows(result.blob, 'b2cs');
    const b2csRow = rows[4]; // Header at 3, data at 4
    expect(b2csRow[0]).toBe('Punjab');
    expect(b2csRow[1]).toBe(18);
    expect(b2csRow[2]).toBe(15000); // 10000 + 5000
    expect(b2csRow[4]).toBe(1350); // 900 + 450
    expect(b2csRow[7]).toBe('Apr-2022'); // Source_Period appended
  });
});
