import React, { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/layout/PageLayout';
import PageHeader from '../components/common/PageHeader';
import ContentCard from '../components/cards/ContentCard';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import { useAuth } from '../context/AuthContext';
import { API_BASE, apiFetch } from '../api/client';
import LoadingState from '../components/common/LoadingState';
import theme from '../theme/theme';
import { cn } from '../lib/utils';

function AdminPageContent() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch(`${API_BASE}/api/admin/users`),
      apiFetch(`${API_BASE}/api/admin/audit-logs?limit=15`),
      apiFetch(`${API_BASE}/api/admin/health`),
    ]).then(([u, l, h]) => {
      setUsers(u.users || []);
      setLogs(l.logs || []);
      setHealth(h);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState message="Loading administration…" testId="admin-loading" />;

  return (
    <DashboardLayout>
      <PageHeader title="Administration" description="Users, audit logs, and system health." testId="admin-page-header" />
      <div className="grid gap-6 lg:grid-cols-2">
        <ContentCard title="Users" testId="admin-users">
          <ul className="text-sm space-y-2">
            {users.map((u) => (
              <li key={u.user_id} className="flex justify-between border-b border-border/40 pb-2" data-testid={`admin-user-${u.username}`}>
                <span>{u.full_name || u.username}</span>
                <span className="text-muted-foreground">{u.roles?.join(', ')} · {u.status}</span>
              </li>
            ))}
          </ul>
        </ContentCard>
        <ContentCard title="System Health" testId="admin-health">
          {health && (
            <dl className="text-sm space-y-1">
              <div className="flex justify-between"><dt>Status</dt><dd>{health.status}</dd></div>
              <div className="flex justify-between"><dt>Database</dt><dd>{health.database}</dd></div>
              <div className="flex justify-between"><dt>Workers</dt><dd>{health.worker_count}</dd></div>
              <div className="flex justify-between"><dt>Active sessions</dt><dd>{health.active_sessions}</dd></div>
              <div className="flex justify-between"><dt>Users</dt><dd>{health.user_count}</dd></div>
            </dl>
          )}
        </ContentCard>
        <ContentCard title="Audit Logs" testId="admin-audit-logs" className="lg:col-span-2">
          <ul className="text-xs space-y-1 max-h-64 overflow-auto">
            {logs.map((l) => (
              <li key={l.log_id} className="grid grid-cols-4 gap-2 border-b border-border/30 py-1">
                <span>{l.timestamp?.slice(0, 19)}</span>
                <span>{l.username}</span>
                <span>{l.action}</span>
                <span className="text-muted-foreground truncate">{l.session_id || l.gstin || l.result}</span>
              </li>
            ))}
          </ul>
        </ContentCard>
      </div>
      <p className={cn(theme.text.label, 'mt-4')}>Signed in as {user?.username}</p>
    </DashboardLayout>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute permission="view_admin">
      <AdminPageContent />
    </ProtectedRoute>
  );
}
