import React from 'react';
import { DATASET_KEYS, DATASET_LABELS } from '../../types/auditSession';
import ContentCard from '../cards/ContentCard';
import ProgressCard from '../cards/ProgressCard';
import { Icons } from '../../icons';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

export default function ReadinessBar({ readiness, canStart, notReadyReason, datasetKeys }) {
  if (!readiness) return null;

  const keys = datasetKeys?.length ? datasetKeys : DATASET_KEYS;
  const items = keys.map((key) => ({
    key,
    label: DATASET_LABELS[key] || key,
    value: readiness[key] ?? 0,
  }));

  return (
    <ContentCard testId="readiness-panel" noPadding>
      <div className="flex items-center justify-between mb-4">
        <h3 className={theme.text.sectionTitle}>Audit Readiness</h3>
        {!canStart && notReadyReason && (
          <span className="text-xs font-semibold text-warning flex items-center gap-1" data-testid="audit-not-ready">
            <Icons.Alert className={Icons.size.xs} /> Audit Not Ready
          </span>
        )}
      </div>
      {!canStart && notReadyReason && (
        <p className={cn(theme.alert.warning, 'mb-4 text-xs')} data-testid="audit-not-ready-reason">
          {notReadyReason}
        </p>
      )}
      <div className="space-y-3">
        {items.map(({ key, label, value }) => (
          <div key={key}>
            <ProgressCard
              label={label}
              value={value}
              testId={`readiness-${key}`}
            />
          </div>
        ))}
        <div className="pt-2 border-t border-border">
          <ProgressCard label="Overall" value={readiness.overall} testId="readiness-overall" />
        </div>
      </div>
    </ContentCard>
  );
}
