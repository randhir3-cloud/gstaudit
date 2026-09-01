import React from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../cards/ContentCard';
import MetricCard from '../cards/MetricCard';
import ResponsiveGrid from '../layout/ResponsiveGrid';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

const FIELDS = [
  ['missing_invoice', 'Missing Invoice', 'MISSING_IN_GSTR1'],
  ['duplicate_invoice', 'Duplicate Invoice', 'DUPLICATE'],
  ['gstin_mismatch', 'GSTIN Mismatch', 'GSTIN_MISMATCH'],
  ['invoice_mismatch', 'Invoice Mismatch', 'MISSING_IN_EWAY'],
  ['value_mismatch', 'Value Mismatch', 'VALUE_MISMATCH'],
  ['date_mismatch', 'Date Mismatch', 'DATE_MISMATCH'],
  ['hsn_mismatch', 'HSN Mismatch', null],
  ['state_mismatch', 'State Mismatch', null],
  ['risk_score', 'Risk Score', null],
];

export default function DiscrepancySummary({ discrepancies }) {
  const d = discrepancies || {};

  return (
    <ContentCard title="Discrepancy Summary" testId="discrepancy-summary">
      <ResponsiveGrid columns="stats">
        {FIELDS.map(([key, label, filter]) => {
          const inner = (
            <MetricCard
              label={label}
              value={d[key] ?? 0}
              valueTestId={`discrepancy-${key}`}
              size="lg"
              className="text-center"
            />
          );
          return filter ? (
            <Link
              key={key}
              to={`/workbook?filter=${filter}`}
              className="rounded-lg hover:ring-2 hover:ring-primary"
              data-testid={`discrepancy-link-${key}`}
            >
              {inner}
            </Link>
          ) : (
            <div key={key}>{inner}</div>
          );
        })}
      </ResponsiveGrid>
    </ContentCard>
  );
}
