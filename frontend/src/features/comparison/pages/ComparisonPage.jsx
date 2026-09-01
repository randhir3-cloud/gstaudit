import React from 'react';
import { ComparisonLayout } from '../../../components/layout/PageLayout';
import DealerHeader from '../../../components/DealerHeader';
import ErrorState from '../../../components/common/ErrorState';
import EmptyState from '../../../components/common/EmptyState';
import { Button } from '../../../components/ui/button';
import { Link } from 'react-router-dom';
import theme from '../../../theme/theme';
import useComparisonPage from '../hooks/useComparisonPage';
import ComparisonToolbar from '../components/ComparisonToolbar';
import ComparisonSummary from '../components/ComparisonSummary';
import ComparisonObservations from '../components/ComparisonObservations';

export default function ComparisonPage() {
  const {
    hasDealer,
    comparison,
    risk,
    observations,
    loading,
    error,
    pair,
    canRun,
    runComparison,
  } = useComparisonPage();

  return (
    <ComparisonLayout testId="comparison-layout">
      <ComparisonToolbar canRun={canRun} loading={loading} onRun={runComparison} />

      <DealerHeader />

      {error && <ErrorState message={error} testId="comparison-error" />}

      {!hasDealer && (
        <EmptyState
          title="No dealer metadata loaded."
          description="Upload GSTR files on the Merge screen to load dealer metadata."
          className={theme.card.dashed}
          action={(
            <Button variant="link" asChild>
              <Link to="/merge">Go to Merge →</Link>
            </Button>
          )}
        />
      )}

      <ComparisonSummary pair={pair} comparison={comparison} risk={risk} />

      <ComparisonObservations observations={observations} />
    </ComparisonLayout>
  );
}
