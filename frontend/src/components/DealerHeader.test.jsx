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

  it('renders 5 required dealer fields when metadata is provided', () => {
    render(
      <DealerHeaderView
        dealer={{
          gstin: '03AABCU9603R1ZX',
          legal_name: 'UJJIVAN SMALL FINANCE BANK LIMITED',
          trade_name: 'UJJIVAN SMALL FINANCE BANK LIMITED',
          financial_year: '2022-23',
          tax_period: 'April-2022 to March-2023',
        }}
      />,
    );

    expect(screen.getByRole('heading', { name: 'UJJIVAN SMALL FINANCE BANK LIMITED' })).toBeInTheDocument();
    expect(screen.getByText('03AABCU9603R1ZX')).toBeInTheDocument();
    expect(screen.getByText('2022-23')).toBeInTheDocument();
    expect(screen.getByText('April-2022 to March-2023')).toBeInTheDocument();
    expect(screen.getByText('Legal Name')).toBeInTheDocument();
    expect(screen.getByText('Trade Name')).toBeInTheDocument();
  });

  it('renders currentDataset only when showDataset is true', () => {
    render(
      <DealerHeaderView
        dealer={{
          gstin: '03AABCU9603R1ZX',
          legal_name: 'UJJIVAN SMALL FINANCE BANK LIMITED',
          financial_year: '2022-23',
          tax_period: 'April-2022 to March-2023',
        }}
        currentDataset="GSTR2A_Merged.xlsx"
        showDataset={true}
      />,
    );
    expect(screen.getByText('GSTR2A_Merged.xlsx')).toBeInTheDocument();
  });
});
