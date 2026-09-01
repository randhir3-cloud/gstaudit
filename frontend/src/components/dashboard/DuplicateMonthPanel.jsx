import React from 'react';
import { DATASET_LABELS } from '../../types/auditSession';
import ContentCard from '../cards/ContentCard';
import { Button } from '../ui/button';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

export default function DuplicateMonthPanel({ monthCoverage, onResolve }) {
  const duplicates = Object.entries(monthCoverage || {}).flatMap(([key, cov]) =>
    (cov.duplicate_months || []).map((dup) => ({ datasetKey: key, ...dup })),
  );

  if (!duplicates.length) return null;

  return (
    <div className={theme.alert.warning} data-testid="duplicate-panel">
      <h3 className={cn(theme.text.sectionTitle, 'mb-3 text-warning')}>Duplicate Uploads Detected</h3>
      <div className="space-y-4">
        {duplicates.map((dup) => (
          <ContentCard key={`${dup.datasetKey}-${dup.month}`} className={theme.card.background} noPadding>
            <p className={cn(theme.text.body, 'font-semibold')}>{DATASET_LABELS[dup.datasetKey]} — {dup.month}</p>
            <p className={cn(theme.text.muted, 'mt-1')}>{dup.file_count} files uploaded</p>
            <ul className={cn(theme.text.mono, 'mt-2 space-y-1')}>
              {dup.filenames.map((f) => <li key={f}>{f}</li>)}
            </ul>
            <div className="flex gap-2 mt-3">
              {['replace', 'keep_latest', 'delete'].map((action) => (
                <Button
                  key={action}
                  variant="secondary"
                  size="sm"
                  data-testid={`dup-action-${dup.datasetKey}-${action}`}
                  onClick={() => onResolve(dup.datasetKey, dup.month, action, dup.filenames[dup.filenames.length - 1])}
                  className="capitalize text-xs"
                >
                  {action.replace('_', ' ')}
                </Button>
              ))}
            </div>
          </ContentCard>
        ))}
      </div>
    </div>
  );
}
