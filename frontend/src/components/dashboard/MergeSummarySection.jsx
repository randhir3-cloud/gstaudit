import React from 'react';
import { formatCount } from '../../utils/formatNumbers';
import ContentCard from '../cards/ContentCard';
import MetricCard from '../cards/MetricCard';
import ResponsiveGrid from '../layout/ResponsiveGrid';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

export default function MergeSummarySection({ summaries }) {
  if (!summaries?.length) return null;

  return (
    <ContentCard title="Merge Summary" testId="merge-summary">
      <div className="space-y-4">
        {summaries.map((s) => (
          <ContentCard key={s.dataset_key} className="bg-muted/30" testId={`merge-summary-${s.dataset_key}`} noPadding>
            <p className={cn(theme.text.subheading, 'text-base')}>{s.dataset_label}</p>
            <ResponsiveGrid columns="stats" className="mt-3">
              <MetricCard label="Merged Files" value={s.merged_files} />
              <MetricCard label="Rows Imported" value={formatCount(s.rows_imported ?? s.total_rows)} />
              <MetricCard label="Duplicate Records" value={formatCount(s.duplicate_records ?? 0)} />
              <MetricCard label="Rows After Dedup" value={formatCount(s.rows_after_deduplication ?? s.total_rows)} />
              <MetricCard label="Months Covered" value={s.months_covered_count ?? s.months_covered?.length ?? 0} />
              <MetricCard
                label="Processing Time"
                value={s.processing_time_sec ?? (s.processing_time_ms ? `${(s.processing_time_ms / 1000).toFixed(1)} sec` : '—')}
              />
            </ResponsiveGrid>
            <p className={cn(theme.text.muted, 'text-sm mt-3 col-span-full')}>
              Missing Months: <strong className="text-foreground">{s.missing_months?.length ? s.missing_months.join(', ') : 'None'}</strong>
            </p>
            <p className={cn(theme.text.muted, 'text-sm mt-1')}>
              Duplicate Months: <strong className="text-foreground">{s.duplicate_months?.length ? s.duplicate_months.join(', ') : 'None'}</strong>
            </p>
          </ContentCard>
        ))}
      </div>
    </ContentCard>
  );
}
