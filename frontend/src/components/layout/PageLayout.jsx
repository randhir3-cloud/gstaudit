import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';
import PageContainer from '../common/PageContainer';

export default function PageLayout({ children, className, testId }) {
  return (
    <PageContainer className={cn('space-y-6', className)} testId={testId}>
      {children}
    </PageContainer>
  );
}

export function DashboardLayout({ children, className, testId = 'dashboard-layout' }) {
  return (
    <div className={cn('space-y-6', className)} data-testid={testId}>
      {children}
    </div>
  );
}

export function ComparisonLayout({ children, className, testId }) {
  return (
    <PageLayout className={cn('space-y-6', className)} testId={testId}>
      {children}
    </PageLayout>
  );
}

export function InvestigationLayout({ children, className, testId }) {
  return (
    <div className={cn(theme.layout.threePanelLayout, className)} data-testid={testId}>
      {children}
    </div>
  );
}

export function ReportLayout({ children, className, testId }) {
  return (
    <PageLayout className={cn('space-y-6 max-w-5xl', className)} testId={testId}>
      {children}
    </PageLayout>
  );
}
