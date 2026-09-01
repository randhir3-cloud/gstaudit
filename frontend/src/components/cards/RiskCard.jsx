import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';
import { Icons } from '../../icons';

/** Intelligence / risk KPI card */
export default function RiskCard({ label, value, testId, icon: Icon, highlight, className }) {
  return (
    <div
      className={cn(
        'rounded-xl p-3 text-center',
        highlight ? 'bg-danger/10 border border-danger/30' : 'bg-muted',
        className,
      )}
      data-testid={testId}
    >
      <div className={cn('flex items-center justify-center gap-1 mb-1', theme.text.label)}>
        {Icon && <Icon className={Icons.size.xs} aria-hidden />}
        <span className="text-[10px] uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-xl font-bold tabular-nums text-foreground">{value ?? '—'}</p>
    </div>
  );
}
