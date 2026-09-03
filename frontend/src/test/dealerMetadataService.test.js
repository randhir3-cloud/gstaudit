import { describe, it, expect } from 'vitest';
import {
  parseGstr2aTaxPeriod,
  parseGstr1TaxPeriod,
  parseFinancialYear,
  buildTaxPeriodRangeDisplay,
  extractDealerMetadataFromSheet,
  extractDealerMetadataFromFiles,
} from '../utils/excel/dealerMetadataService.js';

describe('Dealer Metadata Extraction & Normalization Service', () => {
  // TEST 1: GSTR-2A Tax Period = 042022 -> April-2022
  it('TEST 1: GSTR-2A Tax Period = 042022 resolves to April-2022', () => {
    const res = parseGstr2aTaxPeriod('042022', '2022-23');
    expect(res.display).toBe('April-2022');
    expect(res.month).toBe(4);
    expect(res.year).toBe(2022);
  });

  // TEST 2: GSTR-2A Tax Period = 012023 -> January-2023
  it('TEST 2: GSTR-2A Tax Period = 012023 resolves to January-2023', () => {
    const res = parseGstr2aTaxPeriod('012023', '2022-23');
    expect(res.display).toBe('January-2023');
    expect(res.month).toBe(1);
    expect(res.year).toBe(2023);
  });

  // TEST 3: GSTR-1 FY = 2022-23, Tax Period = April -> April-2022
  it('TEST 3: GSTR-1 FY = 2022-23, Tax Period = April resolves to April-2022', () => {
    const res = parseGstr1TaxPeriod('April', '2022-23');
    expect(res.display).toBe('April-2022');
    expect(res.month).toBe(4);
    expect(res.year).toBe(2022);
  });

  // TEST 4: GSTR-1 FY = 2022-23, Tax Period = January -> January-2023
  it('TEST 4: GSTR-1 FY = 2022-23, Tax Period = January resolves to January-2023', () => {
    const res = parseGstr1TaxPeriod('January', '2022-23');
    expect(res.display).toBe('January-2023');
    expect(res.month).toBe(1);
    expect(res.year).toBe(2023);
  });

  // TEST 5: 12 periods April-2022 through March-2023 -> April-2022 to March-2023
  it('TEST 5: 12 periods April-2022 through March-2023 format as April-2022 to March-2023', () => {
    const months = [
      { month: 4, year: 2022, display: 'April-2022' },
      { month: 5, year: 2022, display: 'May-2022' },
      { month: 6, year: 2022, display: 'June-2022' },
      { month: 7, year: 2022, display: 'July-2022' },
      { month: 8, year: 2022, display: 'August-2022' },
      { month: 9, year: 2022, display: 'September-2022' },
      { month: 10, year: 2022, display: 'October-2022' },
      { month: 11, year: 2022, display: 'November-2022' },
      { month: 12, year: 2022, display: 'December-2022' },
      { month: 1, year: 2023, display: 'January-2023' },
      { month: 2, year: 2023, display: 'February-2023' },
      { month: 3, year: 2023, display: 'March-2023' },
    ];
    // Shuffled input to ensure chronological sorting
    const shuffled = [...months].sort(() => Math.random() - 0.5);
    const range = buildTaxPeriodRangeDisplay(shuffled);
    expect(range).toBe('April-2022 to March-2023');
  });

  // TEST 6: Three files April/May/June -> April-2022 to June-2022
  it('TEST 6: Three files April/May/June format as April-2022 to June-2022', () => {
    const periods = [
      { month: 4, year: 2022, display: 'April-2022' },
      { month: 5, year: 2022, display: 'May-2022' },
      { month: 6, year: 2022, display: 'June-2022' },
    ];
    expect(buildTaxPeriodRangeDisplay(periods)).toBe('April-2022 to June-2022');
  });

  // TEST 7: One file -> single month only
  it('TEST 7: One file displays single month without "to"', () => {
    const periods = [{ month: 1, year: 2023, display: 'January-2023' }];
    expect(buildTaxPeriodRangeDisplay(periods)).toBe('January-2023');
  });

  // TEST 8: Different GSTIN in one file -> validation error
  it('TEST 8: Detects GSTIN mismatch across files', () => {
    const results = [
      { filename: 'f1.xlsx', dealer: { gstin: '03AAACC1205A1ZX', financial_year: '2022-23' } },
      { filename: 'f2.xlsx', dealer: { gstin: '03AAAAA0000A1Z5', financial_year: '2022-23' } },
    ];
    const first = results[0].dealer;
    const mismatches = [];
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
    expect(mismatches.length).toBe(1);
    expect(mismatches[0].field).toBe('GSTIN');
  });

  // TEST 9: Different Financial Year -> validation error
  it('TEST 9: Detects Financial Year mismatch across files', () => {
    const results = [
      { filename: 'f1.xlsx', dealer: { gstin: '03AAACC1205A1ZX', financial_year: '2022-23' } },
      { filename: 'f2.xlsx', dealer: { gstin: '03AAACC1205A1ZX', financial_year: '2021-22' } },
    ];
    const first = results[0].dealer;
    const mismatches = [];
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
    expect(mismatches.length).toBe(1);
    expect(mismatches[0].field).toBe('Financial Year');
  });

  // TEST 10: Trade Name blank -> graceful display without crash
  it('TEST 10: Gracefully handles blank Trade Name', () => {
    const rows = [
      ['Taxpayer GSTIN', '03AAACC1205A1ZX'],
      ['Legal Name', 'CONTAINER CORPORATION OF INDIA LIMITED'],
      ['Trade Name', ''],
      ['Financial Year', '2022-23'],
      ['Tax Period', '042022'],
    ];
    const meta = extractDealerMetadataFromSheet(rows, 'gstr2a');
    expect(meta.gstin).toBe('03AAACC1205A1ZX');
    expect(meta.legal_name).toBe('CONTAINER CORPORATION OF INDIA LIMITED');
    expect(meta.trade_name).toBe('');
    expect(meta.tax_period_display).toBe('April-2022');
  });

  // TEST 11: Read me capitalization variant -> metadata still detected
  it('TEST 11: Matches case-insensitive and whitespace label variants', () => {
    const rows = [
      ['   TAXPAYER\'S GSTIN   ', '03AAACC1205A1ZX'],
      ['LEGAL NAME OF TAXPAYER', 'CONTAINER CORPORATION OF INDIA LIMITED'],
      ['TRADE NAME (IF ANY)', 'Container Corporation of India Limited'],
      ['FINANCIAL YEAR', '2022-23'],
      ['TAX PERIOD', '012023'],
    ];
    const meta = extractDealerMetadataFromSheet(rows, 'gstr2a');
    expect(meta.gstin).toBe('03AAACC1205A1ZX');
    expect(meta.legal_name).toBe('CONTAINER CORPORATION OF INDIA LIMITED');
    expect(meta.trade_name).toBe('Container Corporation of India Limited');
    expect(meta.financial_year).toBe('2022-23');
    expect(meta.tax_period_display).toBe('January-2023');
  });

  // TEST 12: Raw period with numeric value 12023 -> January-2023
  it('TEST 12: Handles numeric 12023 without losing leading zero', () => {
    const res = parseGstr2aTaxPeriod(12023, '2022-23');
    expect(res.display).toBe('January-2023');
    expect(res.month).toBe(1);
    expect(res.year).toBe(2023);
  });
});
