import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/layout/PageLayout';
import PageHeader from '../components/common/PageHeader';
import ContentCard from '../components/cards/ContentCard';
import EmptyState from '../components/common/EmptyState';
import LoadingState from '../components/common/LoadingState';
import PriorityBadge from '../components/badges/PriorityBadge';
import { Button } from '../components/ui/button';
import { useAuditSession } from '../context/AuditSessionContext';
import { useAuth } from '../context/AuthContext';
import theme from '../theme/theme';
import { cn } from '../lib/utils';
import {
  assignAuditCase,
  fetchAuditCaseDetail,
  fetchAuditCases,
  fetchCaseTransitions,
  issueCaseNotice,
  transitionAuditCase,
  createCaseNotice,
} from '../api/auditCases';

const WORKFLOW_STATUSES = [
  'Draft', 'Assigned', 'Under Investigation', 'Notice Issued',
  'Dealer Response Received', 'Verification Pending', 'Supervisor Review',
  'Approved', 'Closed', 'Archived',
];

function CaseTimeline({ entries }) {
  if (!entries?.length) return <p className="text-xs text-muted-foreground">No timeline events yet.</p>;
  return (
    <ol className="space-y-2 border-l-2 border-border ml-2 pl-4 text-xs" data-testid="case-timeline">
      {entries.map((e) => (
        <li key={e.entry_id} data-testid={`timeline-${e.event_type}`}>
          <span className="font-medium">{e.title}</span>
          <div className="text-muted-foreground">{e.description}</div>
          <div className="text-[10px] text-muted-foreground">{e.actor} · {e.timestamp?.slice(0, 19)}</div>
        </li>
      ))}
    </ol>
  );
}

export default function AuditCaseManagementPage() {
  const { session } = useAuditSession();
  const { user } = useAuth();
  const sessionId = session?.session_id;
  const [cases, setCases] = useState([]);
  const [selected, setSelected] = useState(null);
  const [transitions, setTransitions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [assignForm, setAssignForm] = useState({
    assigned_officer: user?.username || 'officer',
    assigned_supervisor: 'supervisor',
    due_date: '',
    circle: '', ward: '', office: '', department: '',
  });

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await fetchAuditCases(sessionId);
      setCases(data.cases || []);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { load(); }, [load]);

  const openCase = async (auditCaseId) => {
    const detail = await fetchAuditCaseDetail(sessionId, auditCaseId);
    const trans = await fetchCaseTransitions(sessionId, auditCaseId);
    setSelected(detail);
    setTransitions(trans.allowed_transitions || []);
  };

  const handleAssign = async () => {
    if (!selected) return;
    try {
      await assignAuditCase(selected.audit_case_id, {
        session_id: sessionId,
        ...assignForm,
        priority: selected.priority,
      });
      const detail = await fetchAuditCaseDetail(sessionId, selected.audit_case_id);
      const trans = await fetchCaseTransitions(sessionId, selected.audit_case_id);
      setSelected(detail);
      setTransitions(trans.allowed_transitions || []);
      await load();
    } catch (err) {
      console.error(err);
    }
  };

  const handleTransition = async (toStatus) => {
    if (!selected) return;
    await transitionAuditCase(selected.audit_case_id, {
      session_id: sessionId,
      to_status: toStatus,
      actor: user?.username || 'officer',
      reason: `Transitioned to ${toStatus}`,
    });
    await openCase(selected.audit_case_id);
    await load();
  };

  const handleCreateNotice = async () => {
    if (!selected) return;
    const notice = await createCaseNotice(selected.audit_case_id, {
      session_id: sessionId,
      notice_type: 'Show Cause Notice',
      reply_due_date: new Date(Date.now() + 15 * 86400000).toISOString().slice(0, 10),
      notice_content: `Show cause notice for invoice ${selected.invoice_number}`,
    });
    await issueCaseNotice(selected.audit_case_id, notice.notice_id, sessionId, user?.username);
    await openCase(selected.audit_case_id);
    await load();
  };

  return (
    <DashboardLayout testId="audit-case-management">
      <PageHeader
        title="Audit Case Management"
        description="Government GST audit lifecycle — assignment through closure"
        actions={(
          <div className="flex gap-2">
            <Link to="/officer-tasks"><Button size="sm" variant="outline" data-testid="nav-officer-tasks">Officer Tasks</Button></Link>
            <Link to="/supervisor-dashboard"><Button size="sm" variant="outline" data-testid="nav-supervisor">Supervisor</Button></Link>
          </div>
        )}
      />

      {!sessionId && <EmptyState title="No session" description="Load an audit session first." />}

      {sessionId && loading && <LoadingState label="Loading audit cases…" />}

      {sessionId && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <ContentCard testId="audit-cases-list" title="Audit Cases" description={`${cases.length} case(s) from MSAE`}>
            {cases.length === 0 ? (
              <EmptyState title="No cases" description="Run MSAE orchestration from Audit Intelligence first." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b text-muted-foreground">
                      <th className="px-2 py-2 text-left">Case</th>
                      <th className="px-2 py-2 text-left">Invoice</th>
                      <th className="px-2 py-2 text-left">Status</th>
                      <th className="px-2 py-2 text-left">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cases.map((c) => (
                      <tr
                        key={c.audit_case_id}
                        className={cn('border-b cursor-pointer hover:bg-muted/30', selected?.audit_case_id === c.audit_case_id && 'bg-muted/40')}
                        onClick={() => openCase(c.audit_case_id)}
                        data-testid={`audit-case-row-${c.audit_case_id}`}
                      >
                        <td className="px-2 py-2 font-medium">{c.case_number}</td>
                        <td className="px-2 py-2">{c.invoice_number}</td>
                        <td className="px-2 py-2"><PriorityBadge priority={c.workflow_status} label={c.workflow_status} /></td>
                        <td className="px-2 py-2 tabular-nums">{c.risk_score}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </ContentCard>

          <ContentCard testId="audit-case-detail" title={selected ? selected.case_number : 'Case Detail'}>
            {!selected && <EmptyState title="Select a case" description="Click a case to manage workflow." />}
            {selected && (
              <div className="space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-muted-foreground">Status:</span> {selected.workflow_status}</div>
                  <div><span className="text-muted-foreground">Officer:</span> {selected.assigned_officer || '—'}</div>
                  <div><span className="text-muted-foreground">Due:</span> {selected.due_date || '—'}</div>
                  <div><span className="text-muted-foreground">Risk:</span> {selected.risk_score}</div>
                </div>

                {selected.workflow_status === 'Draft' && (
                  <div className="space-y-2 border rounded-lg p-3" data-testid="assign-form">
                    <h4 className="font-semibold text-xs">Assign Case</h4>
                    <input className="w-full border rounded px-2 py-1 text-xs" placeholder="Officer" value={assignForm.assigned_officer} onChange={(e) => setAssignForm({ ...assignForm, assigned_officer: e.target.value })} data-testid="assign-officer" />
                    <input className="w-full border rounded px-2 py-1 text-xs" placeholder="Supervisor" value={assignForm.assigned_supervisor} onChange={(e) => setAssignForm({ ...assignForm, assigned_supervisor: e.target.value })} />
                    <input type="date" className="w-full border rounded px-2 py-1 text-xs" value={assignForm.due_date} onChange={(e) => setAssignForm({ ...assignForm, due_date: e.target.value })} data-testid="assign-due-date" />
                    <input className="w-full border rounded px-2 py-1 text-xs" placeholder="Circle" value={assignForm.circle} onChange={(e) => setAssignForm({ ...assignForm, circle: e.target.value })} />
                    <Button size="sm" onClick={handleAssign} data-testid="assign-submit">Assign</Button>
                  </div>
                )}

                {transitions.length > 0 && (
                  <div data-testid="transition-actions">
                    <h4 className="font-semibold text-xs mb-2">Workflow Actions</h4>
                    <div className="flex flex-wrap gap-2">
                      {transitions.map((s) => (
                        <Button key={s} size="sm" variant="outline" onClick={() => handleTransition(s)} data-testid={`transition-${s.replace(/\s+/g, '-')}`}>
                          → {s}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {selected.workflow_status === 'Under Investigation' && (
                  <Button size="sm" onClick={handleCreateNotice} data-testid="generate-notice">Generate & Issue Notice</Button>
                )}

                {selected.notices?.length > 0 && (
                  <div data-testid="case-notices">
                    <h4 className="font-semibold text-xs mb-1">Notices</h4>
                    {selected.notices.map((n) => (
                      <div key={n.notice_id} className="text-xs border rounded px-2 py-1 mb-1">
                        {n.notice_number} — {n.notice_type} ({n.notice_status})
                      </div>
                    ))}
                  </div>
                )}

                <div>
                  <h4 className={cn(theme.text.label, 'font-semibold mb-2')}>Case Timeline</h4>
                  <CaseTimeline entries={selected.timeline} />
                </div>
              </div>
            )}
          </ContentCard>
        </div>
      )}
    </DashboardLayout>
  );
}
