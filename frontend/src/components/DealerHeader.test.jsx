import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DealerHeaderView } from '../components/DealerHeader';

describe('DealerHeader', () => {
  it('shows placeholder when no dealer is loaded', () => {
    render(
      <DealerHeaderView dealer={{ gstin: '' }} currentDataset="" />,
    );
    expect(screen.getByText(/Upload GSTR-1 or GSTR-2A files/i)).toBeInTheDocument();
  });

  it('renders dealer fields when metadata is provided', () => {
    render(
      <DealerHeaderView
        dealer={{
          gstin: '03AABCU9603R1ZX',
          legal_name: 'UJJIVAN SMALL FINANCE BANK LIMITED',
          trade_name: 'UJJIVAN SMALL FINANCE BANK LIMITED',
          financial_year: '2022-23',
          tax_period: 'April 2022 to March 2023',
        }}
        currentDataset="GSTR2A_Merged.xlsx"
      />,
    );

    expect(screen.getByRole('heading', { name: 'UJJIVAN SMALL FINANCE BANK LIMITED' })).toBeInTheDocument();
    expect(screen.getByText('03AABCU9603R1ZX')).toBeInTheDocument();
    expect(screen.getByText('2022-23')).toBeInTheDocument();
    expect(screen.getByText('GSTR2A_Merged.xlsx')).toBeInTheDocument();
  });
});
