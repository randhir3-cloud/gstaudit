import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';
import { Icons } from '../../icons';
import DatasetBadge from '../badges/DatasetBadge';
import { Button } from '../ui/button';
import { formatCount, formatPercent, formatDate } from '../../utils/formatNumbers';
import ContentCard from './ContentCard';

export default function DatasetCard({ card }) {
  const statusLabel = card.status || 'Empty';
  const monthsLabel = `${card.months_uploaded ?? 0} / ${card.months_total ?? 12}`;

  return (
    <ContentCard testId={`dataset-card-${card.dataset_key}`} noPadding>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <Icons.Spreadsheet className="h-5 w-5 text-primary" />
          <h3 className={theme.text.sectionTitle}>{card.name}</h3>
        </div>
        <DatasetBadge status={statusLabel} />
      </div>
      <dl className="grid grid-cols-2 gap-3 text-sm">
        <Field label="Dealer" value={card.dealer_name} className="col-span-2" />
        <Field label="GSTIN" value={card.dealer_gstin} mono className="col-span-2" />
        <Field label="Financial Year" value={card.financial_year} />
        <Field label="Files Uploaded" value={card.files_uploaded} bold />
        <Field label="Months Uploaded" value={monthsLabel} testId={`months-${card.dataset_key}`} bold />
        <Field label="Rows Imported" value={formatCount(card.rows_imported ?? card.rows)} bold />
        <Field label="Duplicate Records" value={formatCount(card.duplicate_records ?? 0)} warning bold />
        <Field label="Unique Records" value={formatCount(card.unique_records ?? card.rows)} bold />
        <Field label="Merge Status" value={card.merge_status || (card.merged ? 'Completed' : 'Pending')} />
        <Field label="Last Upload" value={card.last_upload ? formatDate(card.last_upload) : '—'} className="col-span-2" small />
      </dl>
      {card.duplicate_percent > 0 && (
        <p className="mt-2 text-xs text-warning">
          Duplicate rate: {formatPercent(card.duplicate_percent)}
        </p>
      )}
      {card.missing_months?.length > 0 && (
        <p className="mt-3 text-xs text-warning" data-testid={`missing-${card.dataset_key}`}>
          Missing: {card.missing_months.join(', ')}
        </p>
      )}
      <div className="mt-4 flex gap-2">
        <Button variant="secondary" size="sm" className="flex-1" asChild>
          <Link to="/merge"><Icons.Eye className={Icons.size.xs} /> Preview</Link>
        </Button>
        <Button size="sm" className="flex-1" asChild>
          <Link to="/workbook"><Icons.Download className={Icons.size.xs} /> Summary</Link>
        </Button>
      </div>
    </ContentCard>
  );
}

function Field({ label, value, mono, bold, warning, small, className, testId }) {
  return (
    <div className={className}>
      <dt className={theme.text.label}>{label}</dt>
      <dd
        className={cn(
          mono && theme.text.mono,
          bold && 'font-semibold tabular-nums',
          warning && 'text-warning',
          small && 'text-xs',
          !mono && 'font-medium truncate',
        )}
        data-testid={testId}
      >
        {value || '—'}
      </dd>
    </div>
  );
}
