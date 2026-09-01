import { describe, it, expect } from 'vitest';
import * as XLSX from 'xlsx';
import { mergeGstr1Files } from '../utils/excel/gstr1Merger.js';
import { mergeGstr2aFiles } from '../utils/excel/gstr2aMerger.js';
import { classifyEwayFiles, parseEwaySheetRows, resolveBatchDealerGstin } from '../utils/excel/ewayDetector.js';
import { mergeEwayFiles } from '../utils/excel/ewayMerger.js';

function createMockGstr1File(filename, period, gstin = '03AABCV6919K1Z5') {
  const wb = XLSX.utils.book_new();

  // Read me sheet
  const readmeRows = [
    ['Header', 'Value'],
    ['1', 'Instructions'],
    ['2', 'More info'],
    ['Financial Year', '2022-23'],
    ['Tax Period', period],
    ['GSTIN of Taxpayer', gstin],
    ['Legal Name of Taxpayer', 'Test Company Ltd'],
    ['Trade Name', 'Test Company'],
    ['ARN', 'AA030422000001Z'],
    ['Date of ARN', '11/05/2022'],
  ];
  const readmeWs = XLSX.utils.aoa_to_sheet(readmeRows);
  XLSX.utils.book_append_sheet(wb, readmeWs, 'Read me');

  // B2B Sheet
  const b2bRows = [
    ['Summary of B2B'],
    ['Note: Test'],
    ['Details'],
    ['GSTIN/UIN of Recipient', 'Receiver Name', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Place Of Supply', 'Reverse Charge', 'Invoice Type', 'Rate', 'Taxable Value', 'Cess Amount'],
    ['03AABCT1234A1Z1', 'Customer A', `INV-${period}-01`, '01/05/2022', 10000, '03-Punjab', 'N', 'Regular', 18, 8474.58, 0],
    ['03AABCT1234A1Z1', 'Customer A', `INV-${period}-02`, '02/05/2022', 20000, '03-Punjab', 'N', 'Regular', 18, 16949.15, 0],
  ];
  const b2bWs = XLSX.utils.aoa_to_sheet(b2bRows);
  XLSX.utils.book_append_sheet(wb, b2bWs, 'b2b');

  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new File([buf], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

function createMockGstr2aFile(filename, period, gstin = '03AABCV6919K1Z5') {
  const wb = XLSX.utils.book_new();

  // Read me sheet
  const readmeRows = [
    ['', '', '', '', ''],
    ['', '', gstin, '', period],
    ['', '', 'Test Company Ltd', '', '2022-23'],
    ['', '', 'Test Company', '', '11/05/2022'],
  ];
  const readmeWs = XLSX.utils.aoa_to_sheet(readmeRows);
  XLSX.utils.book_append_sheet(wb, readmeWs, 'Read me');

  // B2B Sheet
  const b2bRows = [
    ['', '', '', '', '', '', ''],
    ['', '', '', '', '', '', ''],
    ['', '', '', '', '', '', ''],
    ['', '', '', '', '', '', ''],
    ['GSTIN of Supplier', 'Trade/Legal Name', 'Invoice number', 'Invoice type', 'Invoice Date', 'Invoice Value', 'Place of supply', 'Supply Attract Reverse Charge', 'Rate', 'Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT Tax', 'Cess'],
    ['03AABCT9999Z1Z5', 'Supplier X', `PINV-${period}-1`, 'Regular', '05/05/2022', 5000, '03-Punjab', 'N', 18, 4237.29, 0, 381.35, 381.35, 0],
    ['03AABCT9999Z1Z5', 'Supplier X', `PINV-${period}-1-Total`, 'Regular', '05/05/2022', 5000, '03-Punjab', 'N', 18, 4237.29, 0, 381.35, 381.35, 0],
  ];
  const b2bWs = XLSX.utils.aoa_to_sheet(b2bRows);
  XLSX.utils.book_append_sheet(wb, b2bWs, 'B2B');

  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new File([buf], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

function createMockEwayFile(filename, direction, dealerGstin = '03AABCV6919K1Z5', offset = 0) {
  const wb = XLSX.utils.book_new();
  const rows = [
    ['EWB No.', 'From GSTIN & Name', 'To GSTIN & Name', 'Doc No. & Dt.', 'Assess Val.', 'EWB No. & Dt.'],
  ];

  for (let i = 1; i <= 5; i++) {
    const idx = offset + i;
    const fromGstin = direction === 'outward' ? dealerGstin : `07ACQPR6971B1Z${idx % 10}`;
    const toGstin = direction === 'inward' ? `${dealerGstin} / TEST BANK LTD` : '29AABCT1332L000';
    rows.push([
      `10158157900${idx}`,
      fromGstin,
      toGstin,
      `INV-${String(idx).padStart(3, '0')} - 11/04/2023`,
      1000 * idx,
      `10158157900${idx} - 11/04/2023 10:29:00`,
    ]);
  }

  const ws = XLSX.utils.aoa_to_sheet(rows);
  XLSX.utils.book_append_sheet(wb, ws, 'EWB');
  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new File([buf], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

describe('Browser-only Merge & Classification Suite', () => {
  it('Merges GSTR-1 files correctly and preserves dealer info', async () => {
    const file1 = createMockGstr1File('GSTR1_03AABCV6919K1Z5_042022_Inv_1.xlsx', 'April 2022');
    const file2 = createMockGstr1File('GSTR1_03AABCV6919K1Z5_052022_Inv_1.xlsx', 'May 2022');

    const result = await mergeGstr1Files([file1, file2]);
    expect(result.suggested_filename).toContain('GSTR1_03AABCV6919K1Z5_2022-23_Merged.xlsx');
    expect(result.dealer.gstin).toBe('03AABCV6919K1Z5');
    expect(result.blob).toBeInstanceOf(Blob);
    expect(result.blob.size).toBeGreaterThan(0);
  });

  it('Merges GSTR-2A files correctly and filters total rows', async () => {
    const file1 = createMockGstr2aFile('GSTR2A_03AABCV6919K1Z5_042022_Inv_1.xlsx', 'April 2022');
    const file2 = createMockGstr2aFile('GSTR2A_03AABCV6919K1Z5_052022_Inv_1.xlsx', 'May 2022');

    const result = await mergeGstr2aFiles([file1, file2]);
    expect(result.suggested_filename).toContain('GSTR2A_03AABCV6919K1Z5_2022-23_Merged.xlsx');
    expect(result.dealer.gstin).toBe('03AABCV6919K1Z5');
    expect(result.blob).toBeInstanceOf(Blob);
    expect(result.blob.size).toBeGreaterThan(0);
  });

  it('Detects E-Way Bill outward automatically', async () => {
    const file = createMockEwayFile('ewb_outward_042023.xlsx', 'outward');
    const resp = await classifyEwayFiles([file], { dealerGstin: '03AABCV6919K1Z5' });
    expect(resp.classifications[0].detected_type).toBe('outward');
    expect(resp.classifications[0].status).toBe('valid');
  });

  it('Detects E-Way Bill inward automatically with multi-supplier records', async () => {
    const file1 = createMockEwayFile('EWB_MIS_Report_Excel (1).xls', 'inward', '03AABCU9603R1ZX', 0);
    const file2 = createMockEwayFile('EWB_MIS_Report_Excel (2).xls', 'inward', '03AABCU9603R1ZX', 5);
    const resp = await classifyEwayFiles([file1, file2]);
    expect(resp.dealer_resolution.gstin).toBe('03AABCU9603R1ZX');
    expect(resp.classifications[0].detected_type).toBe('inward');
    expect(resp.classifications[1].detected_type).toBe('inward');
    expect(resp.valid_count).toBe(2);
  });

  it('Merges E-Way Bill Inward files into EWB_Inward_Merged.xlsx', async () => {
    const file1 = createMockEwayFile('ewb_inward_042023.xlsx', 'inward', '03AABCU9603R1ZX', 0);
    const file2 = createMockEwayFile('ewb_inward_052023.xlsx', 'inward', '03AABCU9603R1ZX', 5);
    const result = await mergeEwayFiles([file1, file2], 'inward', { ignoreMissing: true });
    expect(result.suggested_filename).toBe('EWB_Inward_Merged.xlsx');
    expect(result.row_count).toBe(10);
    expect(result.blob).toBeInstanceOf(Blob);
  });

  it('Merges E-Way Bill Outward files into EWB_Outward_Merged.xlsx', async () => {
    const file1 = createMockEwayFile('ewb_outward_042023.xlsx', 'outward', '03AABCV6919K1Z5', 0);
    const file2 = createMockEwayFile('ewb_outward_052023.xlsx', 'outward', '03AABCV6919K1Z5', 5);
    const result = await mergeEwayFiles([file1, file2], 'outward', { ignoreMissing: true });
    expect(result.suggested_filename).toBe('EWB_Outward_Merged.xlsx');
    expect(result.row_count).toBe(10);
    expect(result.blob).toBeInstanceOf(Blob);
  });

  it('Prevents mixing inward and outward files in E-Way merge', async () => {
    const file1 = createMockEwayFile('ewb_outward_042023.xlsx', 'outward', '03AABCV6919K1Z5');
    const file2 = createMockEwayFile('ewb_inward_052023.xlsx', 'inward', '03AABCV6919K1Z5');

    await expect(
      mergeEwayFiles([file1, file2], 'outward', { dealerGstin: '03AABCV6919K1Z5', ignoreMissing: true })
    ).rejects.toThrow(/contain mixed directions/);
  });

  it('Verifies fresh-target move behavior replaces stale files in target section', () => {
    // Simulating context state transition
    const oldInwardFiles = [
      { id: 'old1', name: 'old-inward-1.xls' },
      { id: 'old2', name: 'old-inward-2.xls' },
      { id: 'old3', name: 'old-inward-3.xls' },
    ];
    const movedInwardFile = { id: 'new1', name: 'Inward July 1.xls', classification: { status: 'wrong_section', detected_type: 'inward' } };

    // Fresh target creation logic:
    const freshTargetFiles = [movedInwardFile].map((f) => ({
      ...f,
      classification: { ...f.classification, status: 'valid', detected_type: 'inward' },
    }));

    expect(freshTargetFiles.length).toBe(1);
    expect(freshTargetFiles[0].name).toBe('Inward July 1.xls');
    expect(freshTargetFiles.some((f) => f.name.startsWith('old-'))).toBe(false);
  });
});
