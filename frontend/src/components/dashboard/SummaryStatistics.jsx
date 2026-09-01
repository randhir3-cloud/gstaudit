import React from 'react';
import { DATASET_LABELS } from '../../types/auditSession';
import { formatCount, formatPercent } from '../../utils/formatNumbers';
import ContentCard from '../cards/ContentCard';
import MetricCard from '../cards/MetricCard';
import ResponsiveGrid from '../layout/ResponsiveGrid';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

export default function SummaryStatistics({ statistics, summary }) {
  const modules = Object.entries(statistics || {});

  return (
    <ContentCard title="Dataset Statistics" testId="summary-statistics">
      <ResponsiveGrid columns="stats" className="mb-6 p-4 rounded-xl bg-muted">
        <MetricCard label="Total Files" value={formatCount(summary?.files_uploaded)} testId="stat-total-files" />
        <MetricCard label="Total Rows" value={formatCount(summary?.total_rows)} testId="stat-total-rows" />
        <MetricCard label="Unique Records" value={formatCount(summary?.unique_records)} testId="stat-unique-records" />
        <MetricCard label="Duplicate Records" value={formatCount(summary?.duplicate_records)} testId="stat-duplicate-records" />
        <MetricCard label="Duplicate %" value={formatPercent(summary?.duplicate_percent)} testId="stat-dup-pct" />
        <MetricCard label="E-Way Bills" value={formatCount(summary?.total_eway_bills)} testId="stat-total-eway" />
      </ResponsiveGrid>
      <div className="space-y-4">
        {modules.map(([key, stats]) => (
          <div key={key} className="border-t border-border pt-3" data-testid={`stats-${key}`}>
            <p className={cn(theme.text.body, 'font-semibold mb-2')}>{DATASET_LABELS[key] || key}</p>
            <div className={cn('grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs', theme.text.muted)}>
              <span>Files: {stats.files_uploaded}</span>
              <span>Rows: {formatCount(stats.total_rows)}</span>
              <span>Unique: {formatCount(stats.unique_records)}</span>
              <span>Dup: {formatCount(stats.duplicate_records)} ({formatPercent(stats.duplicate_percent)})</span>
            </div>
          </div>
        ))}
      </div>
    </ContentCard>
  );
}
