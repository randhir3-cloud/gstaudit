import React from 'react';
import { InvestigationLayout } from '../../../components/layout/PageLayout';
import EmptyState from '../../../components/common/EmptyState';
import ContentCard from '../../../components/cards/ContentCard';
import theme from '../../../theme/theme';
import useInvestigationPage from '../hooks/useInvestigationPage';
import InvestigationToolbar from '../components/InvestigationToolbar';
import CaseSidebar from '../components/CaseSidebar';
import CaseFilters from '../components/CaseFilters';
import CaseActions from '../components/CaseActions';
import CaseTable from '../components/CaseTable';
import { CaseDetailsContent } from '../components/CaseDetails';

export default function InvestigationPage() {
  const {
    sessionId,
    data,
    category,
    setCategory,
    selectedCase,
    setSelectedCase,
    selectedIds,
    loading,
    saving,
    filters,
    setFilters,
    saveCase,
    bulkUpdate,
    toggleSelect,
    selectAll,
  } = useInvestigationPage();

  return (
    <div className="space-y-4">
      <InvestigationToolbar />

      {!sessionId && (
        <EmptyState
          title="No audit session loaded."
          description="Load an audit session and run comparison first."
          className={theme.card.dashed}
        />
      )}

      <InvestigationLayout testId="investigation-layout">
        <CaseSidebar
          active={category}
          onSelect={setCategory}
          categories={data?.categories}
          summary={data?.summary}
        />

        <div className="space-y-3">
          <ContentCard testId="investigation-grid" noPadding>
            <CaseFilters filters={filters} onChange={setFilters} loading={loading} />
            <CaseActions
              selectedCount={selectedIds.length}
              onBulkVerify={() => bulkUpdate('Verified')}
              onBulkPending={() => bulkUpdate('Pending')}
            />
            <CaseTable
              records={data?.cases || []}
              selectable
              selectedIds={selectedIds}
              onSelect={toggleSelect}
              onSelectAll={selectAll}
              onRowClick={setSelectedCase}
              testIdPrefix="investigation"
            />
          </ContentCard>
        </div>

        <CaseDetailsContent caseData={selectedCase} onSave={saveCase} saving={saving} />
      </InvestigationLayout>
    </div>
  );
}
