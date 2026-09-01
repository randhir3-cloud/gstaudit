import React from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../cards/ContentCard';
import MetricCard from '../cards/MetricCard';
import ResponsiveGrid from '../layout/ResponsiveGrid';

export default function CaseTrackingPanel({ tracking }) {
  if (!tracking || !tracking.total) return null;

  const items = [
    { label: 'Open', value: tracking.open, testId: 'cases-open' },
    { label: 'Closed', value: tracking.closed, testId: 'cases-closed' },
    { label: 'Pending', value: tracking.pending, testId: 'cases-pending' },
    { label: 'Verified', value: tracking.verified, testId: 'cases-verified' },
  ];

  return (
    <ContentCard
      testId="case-tracking-panel"
      title="Investigation Cases"
      actions={<Link to="/investigation" className="text-xs text-primary font-medium">Open Workbench →</Link>}
    >
      <ResponsiveGrid columns="stats">
        {items.map(({ label, value, testId }) => (
          <MetricCard key={label} label={label} value={value ?? 0} valueTestId={testId} size="lg" className="text-center" />
        ))}
      </ResponsiveGrid>
    </ContentCard>
  );
}
