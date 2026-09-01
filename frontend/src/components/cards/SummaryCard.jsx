import React from 'react';
import ContentCard from './ContentCard';
import ResponsiveGrid from '../layout/ResponsiveGrid';
import MetricCard from './MetricCard';

export default function SummaryCard({ title, items, testId = 'summary-card' }) {
  if (!items?.length) return null;
  return (
    <ContentCard title={title} testId={testId}>
      <ResponsiveGrid columns="stats">
        {items.map(({ label, value, testId: itemTestId }) => (
          <MetricCard key={label} label={label} value={value} testId={itemTestId} size="lg" />
        ))}
      </ResponsiveGrid>
    </ContentCard>
  );
}
