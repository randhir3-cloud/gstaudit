import React from 'react';
import { cn } from '../../lib/utils';
import { riskClassName, normalizeRiskLabel } from '../../theme/risk';
import { badgeBase } from '../../theme/badges';

export default function PriorityBadge({ priority, score, label, testId = 'priority-badge' }) {
  const level = priority || label;
  const resolved = normalizeRiskLabel(level);
  const display = score != null && score !== '' ? `${level} (${score})` : (level || resolved);

  return (
    <span
      className={cn(badgeBase, 'border', riskClassName(resolved))}
      data-testid={testId}
    >
      {display}
    </span>
  );
}
