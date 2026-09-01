import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/layout/PageLayout';
import PageHeader from '../components/common/PageHeader';
import ContentCard from '../components/cards/ContentCard';
import RiskCard from '../components/cards/RiskCard';
import ResponsiveGrid from '../components/layout/ResponsiveGrid';
import EmptyState from '../components/common/EmptyState';
import LoadingState from '../components/common/LoadingState';
import PriorityBadge from '../components/badges/PriorityBadge';
import { Button } from '../components/ui/button';
import { useAuditSession } from '../context/AuditSessionContext';
import { useAuth } from '../context/AuthContext';
import { Icons } from '../icons';
import { approveAuditCase, fetchSupervisorDashboard } from '../api/auditCases';

export default function SupervisorDashboardPage() {
  const { session } = useAuditSession();
  const { user } = useAuth();
  const sessionId = session?.session_id;
  const [dash, setDash] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      setDash(await fetchSupervisorDashboard(sessionId));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (auditCaseId) => {
    await approveAuditCase(auditCaseId, sessionId, user?.username || 'supervisor', 'Approved after review');
    await load();
  };

  return (
    <DashboardLayout testId="supervisor-dashboard">
      <PageHeader
        title="Supervisor Dashboard"
        description="Pending approvals, officer workload, and risk distribution"
        actions={<Link to="/audit-cases"><Button size="sm" variant="outline">Case Management</Button></Link>}
      />

      {!sessionId && <EmptyState title="No session" description="Load an audit session first." />}
      {sessionId && loading && <LoadingState label="Loading supervisor dashboard…" />}
      {sessionId && dash && (
        <div className="space-y-5">
          <ResponsiveGrid columns="four" testId="supervisor-metrics">
            <RiskCard label="Open Cases" value={dash.total_open} testId="supervisor-open" icon={Icons.Investigate} />
            <RiskCard label="Pending Approval" value={dash.pending_approvals?.length ?? 0} testId="supervisor-pending" icon={Icons.Shield} highlight />
            <RiskCard label="Avg Closure (days)" value={dash.average_closure_days?.toFixed(1) ?? '0'} testId="supervisor-closure" icon={Icons.Calendar} />
            <RiskCard label="Critical Risk" value={dash.risk_distribution?.critical ?? 0} testId="supervisor-critical" icon={Icons.Warning} highlight />
          </ResponsiveGrid>

          <ContentCard testId="pending-approvals" title="Pending Approvals">
            {dash.pending_approvals?.length === 0 ? (
              <p className="text-xs text-muted-foreground">No cases awaiting supervisor review.</p>
            ) : (
              <ul className="space-y-2 text-xs">
                {dash.pending_approvals.map((c) => (
                  <li key={c.audit_case_id} className="flex justify-between items-center border rounded px-3 py-2">
                    <div>
                      <span className="font-medium">{c.case_number}</span>
                      <span className="text-muted-foreground ml-2">{c.invoice_number}</span>
                    </div>
                    <Button size="sm" onClick={() => handleApprove(c.audit_case_id)} data-testid={`approve-${c.audit_case_id}`}>
                      Approve
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </ContentCard>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ContentCard testId="officer-workload" title="Officer Workload">
              <ul className="text-xs space-y-1">
                {(dash.officer_workload || []).map((w) => (
                  <li key={w.officer} className="flex justify-between border-b py-1">
                    <span>{w.officer}</span>
                    <span className="tabular-nums">{w.case_count} cases</span>
                  </li>
                ))}
              </ul>
            </ContentCard>

            <ContentCard testId="cases-by-status" title="Cases by Status">
              <ul className="text-xs space-y-1">
                {Object.entries(dash.cases_by_status || {}).map(([status, count]) => (
                  <li key={status} className="flex justify-between border-b py-1">
                    <PriorityBadge priority={status} label={status} />
                    <span className="tabular-nums">{count}</span>
                  </li>
                ))}
              </ul>
            </ContentCard>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
