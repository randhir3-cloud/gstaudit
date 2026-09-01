import React from 'react';
import { formatCount, formatPercent } from '../../utils/formatNumbers';
import ContentCard from '../cards/ContentCard';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

export default function DuplicateDetectionPanel({ detection }) {
  if (!detection) return null;

  const items = [
    { label: 'Duplicate Files', count: detection.duplicate_files, pct: null },
    { label: 'Duplicate Months', count: detection.duplicate_months, pct: null },
    { label: 'Duplicate Rows', count: detection.duplicate_rows, pct: detection.duplicate_rows_percent },
    { label: 'Duplicate Invoices', count: detection.duplicate_invoices, pct: detection.duplicate_invoices_percent },
    { label: 'Duplicate E-Way Bills', count: detection.duplicate_eway_bills, pct: detection.duplicate_eway_bills_percent },
    { label: 'Duplicate GSTIN + Invoice', count: detection.duplicate_gstin_invoice, pct: detection.duplicate_gstin_invoice_percent },
  ];

  return (
    <ContentCard title="Duplicate Detection" testId="duplicate-detection">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.map(({ label, count, pct }) => (
          <div key={label} className="flex justify-between items-center rounded-lg bg-muted px-3 py-2 text-sm">
            <span className={theme.text.muted}>{label}</span>
            <span className="font-semibold tabular-nums text-foreground">
              {formatCount(count)}
              {pct != null && Number(pct) > 0 && (
                <span className={cn(theme.text.muted, 'text-xs ml-1')}>({formatPercent(pct)})</span>
              )}
            </span>
          </div>
        ))}
      </div>
    </ContentCard>
  );
}
