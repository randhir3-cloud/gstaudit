import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDashboard } from '../hooks/useDashboard';
import { DATASET_LABELS } from '../types/auditSession';
import { DashboardLayout } from '../components/layout/PageLayout';
import PageHeader from '../components/common/PageHeader';
import SectionContainer from '../components/layout/SectionContainer';
import ResponsiveGrid from '../components/layout/ResponsiveGrid';
import LoadingState from '../components/common/LoadingState';
import EmptyState from '../components/common/EmptyState';
import { Button } from '../components/ui/button';
import { Icons } from '../icons';
import theme from '../theme/theme';
import AuditHeader from '../components/dashboard/AuditHeader';
import TopSummaryPanel from '../components/dashboard/TopSummaryPanel';
import DatasetCard from '../components/cards/DatasetCard';
import FinancialYearCalendar from '../components/dashboard/FinancialYearCalendar';
import DuplicateMonthPanel from '../components/dashboard/DuplicateMonthPanel';
import ReadinessBar from '../components/dashboard/ReadinessBar';
import ComparisonStatusCards from '../components/dashboard/ComparisonStatusCards';
import DiscrepancySummary from '../components/dashboard/DiscrepancySummary';
import SummaryStatistics from '../components/dashboard/SummaryStatistics';
import UploadHistoryTable from '../components/dashboard/UploadHistoryTable';
import CaseTrackingPanel from '../components/dashboard/CaseTrackingPanel';
import AuditIntelligencePanel from '../components/dashboard/AuditIntelligencePanel';
import JobQueuePanel from '../components/dashboard/JobQueuePanel';
import SecurityPanel from '../components/dashboard/SecurityPanel';
import MergeSummarySection from '../components/dashboard/MergeSummarySection';
import { useJobs } from '../hooks/useJobs';
import UploadHealthCard from '../components/dashboard/UploadHealthCard';
import DuplicateDetectionPanel from '../components/dashboard/DuplicateDetectionPanel';
import WorkbookSummarySection from '../components/dashboard/WorkbookSummarySection';

export default function Dashboard() {
  const { session, dashboard, loading, refreshDashboard, hasSession, resolveDuplicate } = useDashboard();
  const { jobs, grouped, cancel, retry, loading: jobsLoading } = useJobs(session?.session_id);

  useEffect(() => {
    refreshDashboard();
  }, [session?.updated_at, refreshDashboard]);

  const dash = dashboard || buildFallbackDashboard(session);

  const datasetKeys = dash.dataset_keys || Object.keys(dash.month_coverage || {});

  return (
    <DashboardLayout>
      <PageHeader
        title="GST Audit Dashboard"
        description="Government GST Audit Intelligence — complete upload status at a glance."
        testId="dashboard-page-header"
        actions={(
          <Button asChild>
            <Link to="/merge">
              <Icons.Files className={Icons.size.sm} /> Upload Data
            </Link>
          </Button>
        )}
      />

      {loading && <LoadingState message="Refreshing dashboard…" testId="dashboard-loading" />}

      <AuditHeader dashboard={dash} />

      <SecurityPanel />

      {!hasSession && (
        <EmptyState
          title="No audit session loaded."
          description="Upload GSTR or E-Way Bill files from the Merge screen to begin."
          action={(
            <Button variant="link" asChild>
              <Link to="/merge">Go to Merge →</Link>
            </Button>
          )}
          className={theme.card.dashed}
          testId="dashboard-empty-session"
        />
      )}

      {dash.warnings?.length > 0 && (
        <div className={theme.alert.warning} data-testid="dashboard-warnings">
          {dash.warnings.map((w) => <p key={w}>{w}</p>)}
        </div>
      )}

      <TopSummaryPanel summary={dash.top_summary || dash.summary_statistics} />

      {hasSession && (
        <JobQueuePanel jobs={jobs} grouped={grouped} onCancel={cancel} onRetry={retry} loading={jobsLoading} />
      )}

      {dash.case_tracking?.total > 0 && <CaseTrackingPanel tracking={dash.case_tracking} />}

      {dash.audit_intelligence && <AuditIntelligencePanel intelligence={dash.audit_intelligence} />}

      <SectionContainer title="Dataset Status" testId="dataset-status-section">
        <ResponsiveGrid columns="dashboard">
          {(dash.dataset_cards || []).map((card) => (
            <DatasetCard key={card.dataset_key} card={card} />
          ))}
        </ResponsiveGrid>
      </SectionContainer>

      <SectionContainer title="Financial Year Calendar" testId="month-coverage-section">
        {Object.keys(dash.month_coverage || {}).length > 0 ? (
          <FinancialYearCalendar
            monthCoverage={dash.month_coverage}
            datasetKeys={datasetKeys}
            gstin={dash.gstin}
            onResolveDuplicate={resolveDuplicate}
          />
        ) : hasSession ? (
          <p className={theme.text.muted}>Upload files to see month coverage calendar.</p>
        ) : null}
      </SectionContainer>

      <DuplicateMonthPanel monthCoverage={dash.month_coverage} onResolve={resolveDuplicate} />

      <ResponsiveGrid columns="two">
        <ReadinessBar
          readiness={dash.readiness}
          canStart={dash.can_start_audit}
          notReadyReason={dash.audit_not_ready_reason}
          datasetKeys={datasetKeys}
        />
        <UploadHealthCard health={dash.upload_health} />
      </ResponsiveGrid>

      <ResponsiveGrid columns="two">
        <ComparisonStatusCards pairs={dash.comparison_status} summary={dash.comparison_summary} />
        <DuplicateDetectionPanel detection={dash.duplicate_detection} />
      </ResponsiveGrid>

      <ResponsiveGrid columns="two">
        <SummaryStatistics statistics={dash.statistics} summary={dash.summary_statistics} />
        <DiscrepancySummary discrepancies={dash.discrepancies} />
      </ResponsiveGrid>

      <MergeSummarySection summaries={dash.merge_summaries} />
      <WorkbookSummarySection summaries={dash.workbook_summaries} />
      <UploadHistoryTable history={dash.upload_history} />
    </DashboardLayout>
  );
}

function buildFallbackDashboard(session) {
  return {
    dealer_name: session?.dealer?.legal_name || session?.dealer?.trade_name,
    gstin: session?.dealer?.gstin,
    trade_name: session?.dealer?.trade_name,
    financial_year: session?.financial_year || session?.dealer?.financial_year,
    audit_status: session?.audit_status,
    audit_readiness_percent: 0,
    readiness: { gstr1: 0, gstr2a: 0, ewb_outward: 0, ewb_inward: 0, overall: 0 },
    dataset_keys: Object.keys(session?.datasets || {}),
    dataset_cards: Object.keys(session?.datasets || {}).map((key) => {
      const ds = session.datasets[key];
      return {
        dataset_key: key,
        name: DATASET_LABELS[key],
        files_uploaded: (ds.source_files?.length || 0) + (ds.staged_files?.length || 0),
        rows: ds.row_count,
        invoices: ds.invoice_count,
        merged: ds.merged,
        dealer_gstin: ds.dealer_gstin || session.dealer?.gstin,
        financial_year: ds.financial_year || session.financial_year,
        last_upload: ds.last_upload_at || ds.last_merge_at,
        status: ds.status,
        missing_months: ds.missing_months,
      };
    }),
    month_coverage: {},
    statistics: {},
    summary_statistics: {},
    top_summary: {},
    upload_health: { score_percent: 0, checks: [] },
    duplicate_detection: {},
    workbook_summaries: [],
    comparison_status: [],
    discrepancies: session?.discrepancies,
    upload_history: session?.upload_history,
    merge_summaries: [],
    can_start_audit: false,
    audit_not_ready_reason: '',
    warnings: [],
  };
}
