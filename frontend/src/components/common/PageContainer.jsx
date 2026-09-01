import React from 'react';
import { cn } from '../../lib/utils';
import { pagePadding } from '../../theme/spacing';

export default function PageContainer({ children, className, testId }) {
  return (
    <div className={cn('mx-auto w-full max-w-7xl', pagePadding, className)} data-testid={testId}>
      {children}
    </div>
  );
}
