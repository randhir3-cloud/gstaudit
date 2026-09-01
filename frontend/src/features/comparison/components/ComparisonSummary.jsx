import React from 'react';
import ComparisonDetail from './ComparisonDetail';
import ComparisonBadge from '../../../components/badges/ComparisonBadge';
import ContentCard from '../../../components/cards/ContentCard';
import ResponsiveGrid from '../../../components/layout/ResponsiveGrid';
import MetricCard from '../../../components/cards/MetricCard';
import RiskBadge from '../../../components/common/RiskBadge';
import theme from '../../../theme/theme';
import { cn } from '../../../lib/utils';
import { buildComparisonSummaryItems } from '../constants';

export default function ComparisonSummary({ pair, comparison, risk }) {
  if (!pair) return null;

  const items = buildComparisonSummaryItems(comparison?.summary, risk);

  return (
    <ContentCard testId="comparison-summary-panel" noPadding>
      <div className="flex items-center justify-between mb-4">
        <h3 className={theme.text.sectionTitle}>GSTR-1 ↔ EWB OUTWARD</h3>
        <span data-testid="comparison-run-status">
          <ComparisonBadge status={pair.status} label={String(pair.status).replace('_', ' ')} />
        </span>
      </div>

      {items.length > 0 && (
        <ResponsiveGrid columns="stats" className="mb-4">
          {items.map(({ label, value, testId }) => (
            <MetricCard key={testId} label={label} value={value ?? 0} valueTestId={testId} size="lg" />
          ))}
        </ResponsiveGrid>
      )}

      {risk && (
        <p className={cn(theme.text.body, 'mb-4 flex items-center gap-2')} data-testid="cmp-risk-level">
          Overall Risk: <RiskBadge level={risk.risk_level} score={risk.overall_risk_score} />
        </p>
      )}

      <ComparisonDetail embedded />
    </ContentCard>
  );
}
