import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';

export default function ResponsiveGrid({ children, className, columns = 'responsive', testId }) {
  const gridClass = {
    responsive: theme.layout.responsiveGrid,
    dashboard: theme.layout.dashboardGrid,
    stats: theme.layout.statsGrid,
    two: 'grid grid-cols-1 lg:grid-cols-2 gap-6',
    four: theme.layout.dashboardGrid,
    six: 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4',
  }[columns] || theme.layout.responsiveGrid;

  return (
    <div className={cn(gridClass, className)} data-testid={testId}>
      {children}
    </div>
  );
}
