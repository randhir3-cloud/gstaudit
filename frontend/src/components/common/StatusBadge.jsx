import React from 'react';
import { cn } from '../../lib/utils';
import { statusClassName } from '../../theme/status';
import { badgeBase } from '../../theme/badges';

export default function StatusBadge({ status, label, className, testId, title }) {
  const text = label ?? status ?? '—';
  return (
    <span
      className={cn(badgeBase, statusClassName(status), className)}
      data-testid={testId}
      title={title}
    >
      {text}
    </span>
  );
}
