import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';

export default function MetricCard({ label, value, testId, valueTestId, className, size = 'md' }) {
  const valueClass = size === 'lg' ? 'text-xl font-bold' : 'text-lg font-bold';
  return (
    <div className={cn('rounded-xl bg-muted p-3', className)} data-testid={testId}>
      <p className={theme.text.label}>{label}</p>
      <p className={cn(valueClass, 'tabular-nums mt-1 text-foreground')} data-testid={valueTestId}>{value ?? '—'}</p>
    </div>
  );
}

export function KpiCard(props) {
  return <MetricCard size="lg" {...props} />;
}

export function StatsCard({ label, value, testId, icon: Icon }) {
  return (
    <div className="rounded-xl bg-muted p-3" data-testid={testId}>
      <div className="flex items-center gap-2">
        {Icon && <Icon className="h-4 w-4 text-primary" />}
        <p className={theme.text.label}>{label}</p>
      </div>
      <p className="text-xl font-bold tabular-nums mt-1">{value ?? '—'}</p>
    </div>
  );
}
