import React from 'react';
import { HealthCard } from '../cards/ProgressCard';
import { Icons } from '../../icons';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

const STATUS_ICON = {
  ok: Icons.Check,
  warning: Icons.Warning,
  error: Icons.Alert,
};

const STATUS_COLOR = {
  ok: 'text-success',
  warning: 'text-warning',
  error: 'text-danger',
};

export default function UploadHealthCard({ health }) {
  if (!health) return null;

  return (
    <div className={theme.card.shell} data-testid="upload-health">
      <div className="flex items-center justify-between mb-4">
        <h3 className={theme.text.sectionTitle}>Upload Health</h3>
        <span className="text-2xl font-bold text-primary" data-testid="upload-health-score">
          {health.score_percent}%
        </span>
      </div>
      <ul className="space-y-2">
        {(health.checks || []).map((check) => {
          const Icon = STATUS_ICON[check.status] || Icons.Check;
          const color = STATUS_COLOR[check.status] || STATUS_COLOR.ok;
          const sym = check.passed ? '✓' : check.status === 'warning' ? '⚠' : '✗';
          return (
            <li
              key={check.label}
              className={cn('flex items-start gap-2 text-sm', theme.text.body)}
              data-testid={`health-check-${check.label.replace(/\s+/g, '-').toLowerCase()}`}
            >
              <Icon className={cn(Icons.size.sm, 'mt-0.5 shrink-0', color)} aria-hidden />
              <span><span aria-hidden>{sym}</span> {check.label}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
