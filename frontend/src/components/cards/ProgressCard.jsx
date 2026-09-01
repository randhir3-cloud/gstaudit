import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';

export default function ProgressCard({ label, value = 0, max = 100, testId, footer }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="w-full" data-testid={testId}>
      <div className="flex justify-between text-xs text-muted-foreground mb-1">
        <span>{label}</span>
        <span className="font-bold text-foreground">{Math.round(pct)}%</span>
      </div>
      <div className="h-2.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      {footer}
    </div>
  );
}

export function HealthCard({ title, score, checks, testId }) {
  return (
    <div className={theme.card.shell} data-testid={testId}>
      {title && <h3 className={cn(theme.text.sectionTitle, 'mb-4')}>{title}</h3>}
      {score != null && (
        <ProgressCard label="Health Score" value={score} testId={`${testId}-score`} />
      )}
      {checks?.length > 0 && (
        <ul className={cn('mt-4 space-y-2 text-sm', theme.text.body)}>
          {checks.map((c) => (
            <li key={c.label || c} className="flex justify-between gap-2">
              <span className={theme.text.muted}>{c.label || c}</span>
              <span>{c.status || c.value || '—'}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
