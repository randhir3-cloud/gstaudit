import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../cards/ContentCard';
import StatusBadge from '../common/StatusBadge';
import { useAuth } from '../../context/AuthContext';
import * as authApi from '../../api/auth';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

function formatWhen(iso) {
  if (!iso) return 'Never';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function SecurityPanel() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (!user) return;
    authApi.fetchSessions().then((d) => setSessions(d.sessions || [])).catch(() => {});
    if (user.permissions?.includes('view_audit_logs') || user.roles?.includes('administrator')) {
      authApi.fetchRecentAuditLogs(8).then((d) => setLogs(d.logs || [])).catch(() => {});
    }
  }, [user]);

  if (!user) return null;

  return (
    <ContentCard title="Officer Session" testId="security-panel">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <p className={theme.text.label}>Current User</p>
          <p className={cn(theme.text.body, 'font-medium')} data-testid="current-user-name">{user.full_name || user.username}</p>
          <p className={theme.text.label}>{user.designation || user.roles?.[0] || 'Officer'} · {user.department || 'GST Audit'}</p>
          <p className={theme.text.label} data-testid="last-login">Last login: {formatWhen(user.last_login_at)}</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {(user.roles || []).map((r) => (
              <StatusBadge key={r} status="active" label={r} testId={`user-role-${r}`} />
            ))}
          </div>
        </div>
        <div className="space-y-2">
          <p className={theme.text.label}>Open Sessions ({sessions.length})</p>
          <ul className="text-xs space-y-1 max-h-24 overflow-auto" data-testid="open-sessions">
            {sessions.slice(0, 5).map((s) => (
              <li key={s.session_token} className="text-muted-foreground">{s.ip_address || 'unknown'} · {formatWhen(s.last_activity_at)}</li>
            ))}
            {sessions.length === 0 && <li className="text-muted-foreground">No active sessions</li>}
          </ul>
        </div>
      </div>
      <div className="mt-4">
        <p className={theme.text.label}>Recent Activity</p>
        <ul className="text-xs space-y-1 max-h-32 overflow-auto mt-1" data-testid="recent-activity">
          {logs.map((l) => (
            <li key={l.log_id} className="flex justify-between gap-2 border-b border-border/50 py-1">
              <span>{l.action}</span>
              <span className="text-muted-foreground">{formatWhen(l.timestamp)}</span>
            </li>
          ))}
          {logs.length === 0 && <li className="text-muted-foreground">No recent activity</li>}
        </ul>
        {user.permissions?.includes('view_admin') && (
          <Link to="/admin" className="text-primary text-sm hover:underline mt-2 inline-block" data-testid="admin-panel-link">Administration →</Link>
        )}
      </div>
    </ContentCard>
  );
}
