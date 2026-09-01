import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import EwaySummaryCard from '../components/eway/EwaySummaryCard';
import { resolveBatchDealerGstin } from '../utils/excel/ewayDetector';

describe('E-Way Summary Card & Metadata Resolution', () => {
  it('Resolves Dealer GSTIN, Legal Name, and Financial Year from parsed batch data', () => {
    const mockParsedFiles = [
      {
        filename: 'Inward July 1.xls',
        fromColIdx: 1,
        toColIdx: 2,
        ewbDateColIdx: 5,
        dataRows: [
          [
            '251452970245',
            '27AAICS9442B1ZA / SURAJ INFORMATICS PRIVATE LIMITED',
            '03AAACC1205A1ZX / CONTAINER CORPORATION OF INDIA LTD',
            'KOLKATA',
            'Ludhiana',
            '251452970245 - 09/07/2022 18:34:00',
          ],
        ],
      },
      {
        filename: 'Inward April 1.xls',
        fromColIdx: 1,
        toColIdx: 2,
        ewbDateColIdx: 5,
        dataRows: [
          [
            '371435607633',
            '27AAICS9442B1ZA / SURAJ INFORMATICS PRIVATE LIMITED',
            '03AAACC1205A1ZX / CONTAINER CORPORATION OF INDIA LTD',
            'KOLKATA',
            'Ludhiana',
            '371435607633 - 14/04/2022 17:59:00',
          ],
        ],
      },
    ];

    const resolution = resolveBatchDealerGstin(mockParsedFiles);
    expect(resolution.gstin).toBe('03AAACC1205A1ZX');
    expect(resolution.source).toBe('inward_batch');
    expect(resolution.legal_name).toBe('CONTAINER CORPORATION OF INDIA LTD');
    expect(resolution.financial_year).toBe('2022-23');
    expect(resolution.total_rows).toBe(2);
  });

  it('Correctly renders populated Dealer Name, GSTIN, Financial Year, and Total Rows on EwaySummaryCard', () => {
    const workflow = {
      dealerMetadata: {
        gstin: '03AAACC1205A1ZX',
        legal_name: 'CONTAINER CORPORATION OF INDIA LTD',
        trade_name: 'CONTAINER CORPORATION OF INDIA LTD',
        financial_year: '2022-23',
      },
      summary: {
        financial_year: '2022-23',
        row_count: 68,
      },
      mergeStatus: 'idle',
      files: [
        {
          id: 'f1',
          name: 'Inward April 1.xls',
          classification: {
            dealer_gstin: '03AAACC1205A1ZX',
            month: 'Apr 2022',
            financial_year: '2022-23',
            rows_inspected: 30,
          },
        },
        {
          id: 'f2',
          name: 'Inward July 1.xls',
          classification: {
            dealer_gstin: '03AAACC1205A1ZX',
            month: 'Jul 2022',
            financial_year: '2022-23',
            rows_inspected: 38,
          },
        },
      ],
    };

    render(<EwaySummaryCard workflow={workflow} directionLabel="Inward" />);

    // Assert that Dealer Name, GSTIN, and FY appear inside the summary card
    expect(screen.getByText('CONTAINER CORPORATION OF INDIA LTD')).toBeDefined();
    expect(screen.getByText('03AAACC1205A1ZX')).toBeDefined();
    expect(screen.getByText('2022-23')).toBeDefined();
    expect(screen.getAllByText('2').length).toBe(2); // 2 files, 2 unique months
    expect(screen.getByText('68')).toBeDefined(); // 68 total rows
  });

  it('Resets Summary Card fields when workflow is cleared', () => {
    const emptyWorkflow = {
      dealerMetadata: {
        gstin: '',
        legal_name: '',
        trade_name: '',
        financial_year: '',
      },
      summary: null,
      mergeStatus: 'idle',
      files: [],
    };

    render(<EwaySummaryCard workflow={emptyWorkflow} directionLabel="Inward" />);

    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(3);
    expect(screen.getAllByText('0').length).toBe(2); // 0 files, 0 unique months
  });

  it('Handles multiple FYs cleanly without silent fallback', () => {
    const multiFyFiles = [
      {
        filename: 'Inward 2022.xls',
        fromColIdx: 1,
        toColIdx: 2,
        ewbDateColIdx: 5,
        dataRows: [
          ['1', '27AAICS9442B1ZA', '03AAACC1205A1ZX / CONCOR', '', '', '1 - 10/05/2022 10:00:00'],
        ],
      },
      {
        filename: 'Inward 2023.xls',
        fromColIdx: 1,
        toColIdx: 2,
        ewbDateColIdx: 5,
        dataRows: [
          ['2', '27AAICS9442B1ZA', '03AAACC1205A1ZX / CONCOR', '', '', '2 - 10/05/2023 10:00:00'],
        ],
      },
    ];

    const resolution = resolveBatchDealerGstin(multiFyFiles);
    expect(resolution.financial_year).toBe('2022-23, 2023-24');
  });
});
