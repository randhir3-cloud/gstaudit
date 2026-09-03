import { describe, it, expect } from 'vitest';
import * as XLSX from 'xlsx';
import {
  detectPreviouslyMergedWorkbook,
  computeWorkbookFingerprint,
  buildEwayRecordKey,
  buildGstr1RecordKey,
  buildGstr2aRecordKey,
  createMergeMetadataSheet,
  META_SHEET_NAME,
} from '../utils/excel/duplicateDetection.js';
import { mergeGstr1Files } from '../utils/excel/gstr1Merger.js';
import { mergeGstr2aFiles } from '../utils/excel/gstr2aMerger.js';
import { mergeEwayFiles } from '../utils/excel/ewayMerger.js';
import { classifyEwayFiles } from '../utils/excel/ewayDetector.js';
import { readWorkbookRaw } from '../utils/excel/excelUtils.js';

function createMockGstr1File(filename, period, gstin = '03AABCV6919K1Z5', invOffset = 0) {
  const wb = XLSX.utils.book_new();
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
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(readmeRows), 'Read me');

  const b2bRows = [
    ['Summary of B2B'],
    ['Note: Test'],
    ['Details'],
    ['GSTIN/UIN of Recipient', 'Receiver Name', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Place Of Supply', 'Reverse Charge', 'Invoice Type', 'Rate', 'Taxable Value', 'Cess Amount'],
    ['03AABCT1234A1Z1', 'Customer A', `INV-${1 + invOffset}`, `0${1 + invOffset}/05/2022`, (1 + invOffset) * 10000, '03-Punjab', 'N', 'Regular', 18, (1 + invOffset) * 8474.58, 0],
    ['03AABCT1234A1Z1', 'Customer A', `INV-${2 + invOffset}`, `0${2 + invOffset}/05/2022`, (2 + invOffset) * 10000, '03-Punjab', 'N', 'Regular', 18, (2 + invOffset) * 8474.58, 0],
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(b2bRows), 'b2b');

  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new File([buf], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

function createMockGstr2aFile(filename, period, gstin = '03AABCV6919K1Z5', invOffset = 0) {
  const wb = XLSX.utils.book_new();
  const readmeRows = [
    ['', '', '', '', ''],
    ['', '', gstin, '', period],
    ['', '', 'Test Company Ltd', '', '2022-23'],
    ['', '', 'Test Company', '', '11/05/2022'],
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(readmeRows), 'Read me');

  const b2bRows = [
    ['', '', '', '', '', '', ''],
    ['', '', '', '', '', '', ''],
    ['', '', '', '', '', '', ''],
    ['GSTIN of Supplier', 'Trade/Legal Name', 'Invoice number', 'Invoice type', 'Invoice Date', 'Invoice Value', 'Place of supply', 'Supply Attract Reverse Charge', 'Rate', 'Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT Tax', 'Cess'],
    ['03AABCT9999Z1Z5', 'Supplier X', `PINV-${1 + invOffset}`, 'Regular', '05/05/2022', 5000, '03-Punjab', 'N', 18, 4237.29, 0, 381.35, 381.35, 0],
    ['03AABCT9999Z1Z5', 'Supplier X', `PINV-${1 + invOffset}-Total`, 'Regular', '05/05/2022', 5000, '03-Punjab', 'N', 18, 4237.29, 0, 381.35, 381.35, 0],
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(b2bRows), 'B2B');

  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new File([buf], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

function createMockEwayFile(filename, direction, dealerGstin = '03AABCV6919K1Z5', offset = 0) {
  const wb = XLSX.utils.book_new();
  const rows = [
    ['EWB No.', 'From GSTIN & Name', 'To GSTIN & Name', 'Doc No. & Dt.', 'Assess Val.', 'EWB No. & Dt.'],
  ];

  for (let i = 1; i <= 3; i++) {
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

  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rows), 'EWB');
  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
  return new File([buf], filename, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

describe('Duplicate Protection Suite (3 Layers)', () => {
  describe('Layer 1: Previously Merged Workbook Detection', () => {
    it('Detects and excludes previously merged GSTR-1 workbook with explicit marker', async () => {
      const f1 = createMockGstr1File('GSTR1_03AABCV6919K1Z5_042022_Inv_1.xlsx', 'April 2022', '03AABCV6919K1Z5', 0);
      const f2 = createMockGstr1File('GSTR1_03AABCV6919K1Z5_052022_Inv_1.xlsx', 'May 2022', '03AABCV6919K1Z5', 5);
      const mergeRes = await mergeGstr1Files([f1, f2], { ignoreMissing: true });

      const mergedFile = new File([mergeRes.blob], 'GSTR1_Merged_Output.xlsx');
      const wb = await readWorkbookRaw(mergedFile);
      const detection = detectPreviouslyMergedWorkbook(wb, mergedFile.name);

      expect(detection.isPreviouslyMerged).toBe(true);
      expect(detection.confidence).toBe(1);
      expect(detection.mergeType).toBe('GSTR1');
    });

    it('Detects renamed merged GSTR-1 workbook without _Merged in filename', async () => {
      const f1 = createMockGstr1File('GSTR1_03AABCV6919K1Z5_042022_Inv_1.xlsx', 'April 2022', '03AABCV6919K1Z5', 0);
      const mergeRes = await mergeGstr1Files([f1], { ignoreMissing: true });

      const renamedMergedFile = new File([mergeRes.blob], 'April_Normal_Name.xlsx');
      const wb = await readWorkbookRaw(renamedMergedFile);
      const detection = detectPreviouslyMergedWorkbook(wb, renamedMergedFile.name);

      expect(detection.isPreviouslyMerged).toBe(true);
    });

    it('Detects previously merged GSTR-2A workbook with explicit marker', async () => {
      const f1 = createMockGstr2aFile('GSTR2A_03AABCV6919K1Z5_042022_Inv_1.xlsx', 'April 2022', '03AABCV6919K1Z5', 0);
      const mergeRes = await mergeGstr2aFiles([f1], { ignoreMissing: true });

      const mergedFile = new File([mergeRes.blob], 'GSTR2A_Custom_Name.xlsx');
      const wb = await readWorkbookRaw(mergedFile);
      const detection = detectPreviouslyMergedWorkbook(wb, mergedFile.name);

      expect(detection.isPreviouslyMerged).toBe(true);
      expect(detection.mergeType).toBe('GSTR2A');
    });

    it('Detects previously merged E-Way Inward workbook', async () => {
      const f1 = createMockEwayFile('ewb_inward_042023.xlsx', 'inward', '03AABCV6919K1Z5', 0);
      const mergeRes = await mergeEwayFiles([f1], 'inward', { ignoreMissing: true });

      const mergedFile = new File([mergeRes.blob], 'EWB_Inward_Output.xlsx');
      const wb = await readWorkbookRaw(mergedFile);
      const detection = detectPreviouslyMergedWorkbook(wb, mergedFile.name);

      expect(detection.isPreviouslyMerged).toBe(true);
      expect(detection.mergeType).toBe('EWAY_INWARD');
    });

    it('Detects previously merged E-Way Outward workbook even when renamed to April.xlsx', async () => {
      const f1 = createMockEwayFile('ewb_outward_042023.xlsx', 'outward', '03AABCV6919K1Z5', 0);
      const mergeRes = await mergeEwayFiles([f1], 'outward', { ignoreMissing: true });

      const renamedFile = new File([mergeRes.blob], 'AprilData.xlsx');
      const wb = await readWorkbookRaw(renamedFile);
      const detection = detectPreviouslyMergedWorkbook(wb, renamedFile.name);

      expect(detection.isPreviouslyMerged).toBe(true);
      expect(detection.mergeType).toBe('EWAY_OUTWARD');
    });

    it('Marks previously merged file as status="previously_merged" in classifyEwayFiles', async () => {
      const f1 = createMockEwayFile('ewb_inward_042023.xlsx', 'inward', '03AABCV6919K1Z5', 0);
      const mergeRes = await mergeEwayFiles([f1], 'inward', { ignoreMissing: true });
      const mergedFile = new File([mergeRes.blob], 'EWB_Inward_Merged.xlsx');

      const classResp = await classifyEwayFiles([f1, mergedFile], { expectedDirection: 'inward' });
      expect(classResp.classifications[0].status).toBe('valid');
      expect(classResp.classifications[1].status).toBe('previously_merged');
      expect(classResp.previously_merged_count).toBe(1);
    });
  });

  describe('Layer 2: Exact Duplicate Source File Detection via Fingerprint', () => {
    it('Computes identical fingerprint for same file and renamed duplicate file', async () => {
      const f1 = createMockEwayFile('Inward_April.xlsx', 'inward', '03AABCV6919K1Z5', 0);
      const f2 = createMockEwayFile('Inward_April_Copy.xlsx', 'inward', '03AABCV6919K1Z5', 0);

      const fp1 = await computeWorkbookFingerprint(f1);
      const fp2 = await computeWorkbookFingerprint(f2);
      expect(fp1).toBe(fp2);
    });

    it('Marks renamed duplicate file as status="duplicate_file" in E-Way classifier', async () => {
      const f1 = createMockEwayFile('Inward_April.xlsx', 'inward', '03AABCV6919K1Z5', 0);
      const f2 = createMockEwayFile('Inward_April_Copy.xlsx', 'inward', '03AABCV6919K1Z5', 0);

      const resp = await classifyEwayFiles([f1, f2], { expectedDirection: 'inward' });
      expect(resp.classifications[0].status).toBe('valid');
      expect(resp.classifications[1].status).toBe('duplicate_file');
      expect(resp.classifications[1].duplicate_of).toBe('Inward_April.xlsx');
      expect(resp.duplicate_file_count).toBe(1);
    });
  });

  describe('Layer 3: Row-level Duplicate Record Protection', () => {
    it('Deduplicates overlapping records across two different E-Way files', async () => {
      // File 1 has records 1, 2, 3
      const f1 = createMockEwayFile('ewb1.xlsx', 'inward', '03AABCV6919K1Z5', 0);
      // File 2 has records 3, 4, 5 (record 3 is overlapping)
      const f2 = createMockEwayFile('ewb2.xlsx', 'inward', '03AABCV6919K1Z5', 2);

      const result = await mergeEwayFiles([f1, f2], 'inward', { ignoreMissing: true });
      expect(result.row_count).toBe(5); // 1, 2, 3, 4, 5 (not 6)
      expect(result.duplicate_rows_skipped).toBe(1);
    });

    it('Deduplicates overlapping rows in GSTR-1 while preserving unique records', async () => {
      const f1 = createMockGstr1File('GSTR1_03AABCV6919K1Z5_042022_Inv_1.xlsx', '042022', '03AABCV6919K1Z5', 0);
      const f2 = createMockGstr1File('GSTR1_03AABCV6919K1Z5_042022_Inv_2.xlsx', '042022', '03AABCV6919K1Z5', 1); // overlapping INV-2 in same period

      const result = await mergeGstr1Files([f1, f2], { ignoreMissing: true });
      expect(result.duplicate_rows_skipped).toBe(1);
      expect(result.row_count).toBe(3);
    });

    it('Preserves legitimate repeated invoice structures with different tax rates or items', () => {
      const row1 = ['03AABCT1234A1Z1', 'Customer A', 'INV-001', '01/05/2022', 10000, '03-Punjab', 'N', 'Regular', 18, 5000, 0];
      const row2 = ['03AABCT1234A1Z1', 'Customer A', 'INV-001', '01/05/2022', 10000, '03-Punjab', 'N', 'Regular', 12, 5000, 0];
      const headers = ['GSTIN/UIN of Recipient', 'Receiver Name', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Place Of Supply', 'Reverse Charge', 'Invoice Type', 'Rate', 'Taxable Value', 'Cess Amount'];

      const key1 = buildGstr1RecordKey('b2b', row1, headers);
      const key2 = buildGstr1RecordKey('b2b', row2, headers);

      expect(key1).not.toBe(key2); // Different rates produce distinct keys!
    });

    it('Preserves legitimate repeated invoice structures with different taxable values on same invoice', () => {
      const row1 = ['03AABCT1234A1Z1', 'Customer A', 'INV-001', '01/05/2022', 15000, '03-Punjab', 'N', 'Regular', 18, 5000, 0];
      const row2 = ['03AABCT1234A1Z1', 'Customer A', 'INV-001', '01/05/2022', 15000, '03-Punjab', 'N', 'Regular', 18, 10000, 0];
      const headers = ['GSTIN/UIN of Recipient', 'Receiver Name', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Place Of Supply', 'Reverse Charge', 'Invoice Type', 'Rate', 'Taxable Value', 'Cess Amount'];

      const key1 = buildGstr1RecordKey('b2b', row1, headers);
      const key2 = buildGstr1RecordKey('b2b', row2, headers);

      expect(key1).not.toBe(key2); // Different taxable values produce distinct keys!
    });

    it('Preserves E-Way records with same EWB Number but different items/vehicles/tax amounts', () => {
      const row1 = ['101581579001', '03AAACC1205A1ZX', '07ACHPJ8491R1ZN', 'punjab / 144410', 'delhi / 110041', '101581579001 - 19/01/2023', '6734 - 19/01/2023', '10000', '1800', '8609', 'Desc 1', 'RJ27GB7235'];
      const row2 = ['101581579001', '03AAACC1205A1ZX', '07ACHPJ8491R1ZN', 'punjab / 144410', 'delhi / 110041', '101581579001 - 19/01/2023', '6734 - 19/01/2023', '20000', '3600', '8609', 'Desc 2', 'RJ27GB7235'];
      const headers = ['EWB No.', 'From GSTIN & Name', 'To GSTIN & Name', 'From Place & Pin', 'To Place & Pin', 'EWB No. & Dt.', 'Doc No. & Dt.', 'Assess Val.', 'Tax Val.', 'HSN Code', 'HSN Desc.', 'Latest Vehicle No.'];

      const key1 = buildEwayRecordKey(row1, headers);
      const key2 = buildEwayRecordKey(row2, headers);

      expect(key1).not.toBe(key2); // Different Assess Val & Tax Val produce distinct keys!
    });
  });
});
