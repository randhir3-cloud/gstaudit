import React from 'react';
import { cn } from '../../lib/utils';
import { riskClassName, normalizeRiskLabel, scoreToRiskLevel } from '../../theme/risk';
import { badgeBase } from '../../theme/badges';
import StatusBadge from './StatusBadge';

export default function RiskBadge({ level, score, className, testId }) {
  const resolved = level ? normalizeRiskLabel(level) : scoreToRiskLevel(score);
  return (
    <span className={cn(badgeBase, 'border', riskClassName(resolved), className)} data-testid={testId}>
      {resolved}
    </span>
  );
}

export function AuditStatusBadge(props) {
  return <StatusBadge {...props} />;
}
