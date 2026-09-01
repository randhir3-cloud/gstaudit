import React from 'react';
import ContentCard from '../../../components/cards/ContentCard';
import { Icons } from '../../../icons';
import theme from '../../../theme/theme';
import { cn } from '../../../lib/utils';

export default function ComparisonObservations({ observations }) {
  if (!observations?.length) return null;

  return (
    <ContentCard testId="comparison-observations" noPadding>
      <h3 className={cn(theme.text.sectionTitle, 'text-warning mb-3 flex items-center gap-2')}>
        <Icons.Warning className={Icons.size.sm} aria-hidden /> Audit Observations
      </h3>
      <ul className={cn('space-y-3', theme.text.body)}>
        {observations.slice(0, 5).map((o, i) => (
          <li key={i} className={cn(theme.card.shell, 'p-3 border-warning/20 bg-card')}>
            <p className="font-medium">{o.observation}</p>
            {o.officer_action && <p className={cn(theme.text.muted, 'mt-1')}>{o.officer_action}</p>}
          </li>
        ))}
      </ul>
    </ContentCard>
  );
}
