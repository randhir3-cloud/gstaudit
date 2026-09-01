import React from 'react';
import PageHeader from '../../../components/common/PageHeader';
import Toolbar from '../../../components/layout/Toolbar';
import ComparisonActions from './ComparisonActions';

export default function ComparisonToolbar({ canRun, loading, onRun }) {
  return (
    <Toolbar testId="comparison-toolbar">
      <PageHeader
        title="Comparison Engine"
        description="GSTR-1 vs EWB Outward — core audit comparison."
        testId="comparison-page-header"
        className="mb-0 flex-1"
      />
      {canRun && <ComparisonActions loading={loading} onRun={onRun} />}
    </Toolbar>
  );
}
