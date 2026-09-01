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
import { Icons } from '../icons';
import { fetchOfficerTasks } from '../api/auditCases';

function TaskList({ title, cases, testId }) {
  return (
    <ContentCard testId={testId} title={title}>
      {cases?.length === 0 ? (
        <p className="text-xs text-muted-foreground">None</p>
      ) : (
        <ul className="space-y-1.5 text-xs">
          {cases.map((c) => (
            <li key={c.audit_case_id} className="flex justify-between border rounded px-2 py-1.5">
              <Link to="/audit-cases" className="font-medium text-primary">{c.case_number}</Link>
              <PriorityBadge priority={c.priority} label={c.workflow_status} />
            </li>
          ))}
        </ul>
      )}
    </ContentCard>
  );
}

export default function OfficerTasksPage() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [tasks, setTasks] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      setTasks(await fetchOfficerTasks(sessionId));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { load(); }, [load]);

  return (
    <DashboardLayout testId="officer-tasks-page">
      <PageHeader
        title="Officer Task List"
        description="Today's work, overdue cases, and high-risk priorities"
        actions={<Link to="/audit-cases"><Button size="sm" variant="outline">Case Management</Button></Link>}
      />

      {!sessionId && <EmptyState title="No session" description="Load an audit session first." />}
      {sessionId && loading && <LoadingState label="Loading tasks…" />}

      {sessionId && tasks && (
        <div className="space-y-5">
          <ResponsiveGrid columns="four" testId="task-counts">
            <RiskCard label="Today" value={tasks.counts?.today ?? 0} testId="tasks-today" icon={Icons.Calendar} />
            <RiskCard label="Overdue" value={tasks.counts?.overdue ?? 0} testId="tasks-overdue" icon={Icons.Warning} highlight={(tasks.counts?.overdue ?? 0) > 0} />
            <RiskCard label="Due This Week" value={tasks.counts?.due_this_week ?? 0} testId="tasks-week" icon={Icons.Calendar} />
            <RiskCard label="High Risk" value={tasks.counts?.high_risk ?? 0} testId="tasks-high-risk" icon={Icons.Warning} highlight />
          </ResponsiveGrid>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TaskList title="Today's Work" cases={tasks.today} testId="tasks-today-list" />
            <TaskList title="Overdue Cases" cases={tasks.overdue} testId="tasks-overdue-list" />
            <TaskList title="Due This Week" cases={tasks.due_this_week} testId="tasks-week-list" />
            <TaskList title="High-Risk Cases" cases={tasks.high_risk} testId="tasks-high-risk-list" />
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
