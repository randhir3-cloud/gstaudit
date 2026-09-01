import React from 'react';
import ContentCard from '../cards/ContentCard';
import StatusBadge from '../common/StatusBadge';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

export default function MonthCoverageGrid({ datasetKey, label, coverage }) {
  if (!coverage?.months) return null;

  return (
    <ContentCard testId={`month-coverage-${datasetKey}`} title={label} className="p-4">
      <div className="flex flex-wrap gap-1.5">
        {coverage.months.map((m) => (
          <StatusBadge
            key={m.short}
            status={m.uploaded ? 'merged' : 'empty'}
            label={`${m.short} ${m.uploaded ? '✓' : '✗'}`}
            testId={`month-${datasetKey}-${m.short}`}
            className="text-xs"
            title={m.filenames?.join(', ') || ''}
          />
        ))}
      </div>
      {coverage.missing_months?.length > 0 && (
        <p className={cn('mt-2 text-xs text-warning')}>Missing: {coverage.missing_months.join(', ')}</p>
      )}
      {coverage.missing_months?.length === 0 && coverage.uploaded_count > 0 && (
        <p className="mt-2 text-xs text-success">Missing: None</p>
      )}
    </ContentCard>
  );
}
