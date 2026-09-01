import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../../components/ui/button';
import ContentCard from '../../../components/cards/ContentCard';
import { COMPARISON_DETAIL_LINKS } from '../constants';

export default function ComparisonDetail({ className, embedded = false }) {
  const links = (
    <div className="flex flex-wrap gap-2">
      {COMPARISON_DETAIL_LINKS.map(([type, label]) => (
        <Button key={type} variant="secondary" size="sm" asChild>
          <Link to={`/workbook?filter=${type}`} data-testid={`cmp-detail-link-${type}`}>
            {label}
          </Link>
        </Button>
      ))}
    </div>
  );

  if (embedded) return links;

  return (
    <ContentCard title="Detail Views" className={className} testId="comparison-detail-links">
      {links}
    </ContentCard>
  );
}
