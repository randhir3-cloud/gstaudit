import React from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../cards/ContentCard';
import ComparisonBadge from '../badges/ComparisonBadge';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

const FILTER_MAP = {
  missing_invoice: 'MISSING_IN_GSTR1',
  duplicate_invoice: 'DUPLICATE',
  gstin_mismatch: 'GSTIN_MISMATCH',
  invoice_mismatch: 'MISSING_IN_EWAY',
  value_mismatch: 'VALUE_MISMATCH',
  date_mismatch: 'DATE_MISMATCH',
};

export default function ComparisonStatusCards({ pairs, summary }) {
  return (
    <ContentCard title="Comparison Status" testId="comparison-status">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(pairs || []).map((pair) => (
          <div key={pair.id} className={cn('rounded-xl border border-border p-4', theme.card.background, 'bg-muted/30')}>
            <p className={cn(theme.text.body, 'font-semibold')}>{pair.label}</p>
            <span data-testid={`comparison-${pair.id}`}>
              <ComparisonBadge
                status={pair.status}
                label={String(pair.status).replace('_', ' ')}
                className="mt-2 inline-block"
              />
            </span>
            {pair.status === 'completed' && summary && (
              <div className={cn('mt-3 grid grid-cols-2 gap-2 text-xs', theme.text.muted)}>
                <span>Matched: <strong className="text-foreground">{summary.matched_count ?? 0}</strong></span>
                <span>Missing: <strong className="text-foreground">{(summary.missing_in_gstr1_count ?? 0) + (summary.missing_in_eway_count ?? 0)}</strong></span>
                <span>Mismatch: <strong className="text-foreground">{(summary.gstin_mismatch_count ?? 0) + (summary.value_mismatch_count ?? 0)}</strong></span>
                <span>Risk: <strong className="text-foreground" data-testid="comparison-card-risk">{summary.overall_risk_score ?? 0}</strong></span>
              </div>
            )}
            {pair.status === 'completed' && (
              <Link to="/comparison" className="inline-block mt-2 text-xs text-primary font-medium">View details →</Link>
            )}
          </div>
        ))}
      </div>
    </ContentCard>
  );
}

export { FILTER_MAP };
