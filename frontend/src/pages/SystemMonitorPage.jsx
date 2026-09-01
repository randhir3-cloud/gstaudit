import React, { useEffect, useMemo, useState } from 'react';
import { DashboardLayout } from '../components/layout/PageLayout';
import PageHeader from '../components/common/PageHeader';
import ContentCard from '../components/cards/ContentCard';
import MetricCard from '../components/cards/MetricCard';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import LoadingState from '../components/common/LoadingState';
import { Button } from '../components/ui/button';
import { cn } from '../lib/utils';
import theme from '../theme/theme';
import {
  exportSystemLogs,
  fetchSystemHealth,
  fetchSystemLogs,
  fetchSystemMetrics,
  fetchSystemVersion,
} from '../api/system';

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '—';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function formatDuration(seconds) {
  if (seconds == null) return '—';
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  if (hrs > 0) return `${hrs}h ${mins % 60}m`;
  return `${mins}m`;
}

function formatUptime(seconds) {
  if (!seconds) return '—';
  const days = Math.floor(seconds / 86400);
  const hrs = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hrs}h`;
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function StatusBadge({ status, testId }) {
  const tone =
    status === 'healthy' ? 'text-emerald-600 dark:text-emerald-400' :
    status === 'degraded' ? 'text-amber-600 dark:text-amber-400' :
    'text-red-600 dark:text-red-400';
  return (
    <span className={cn('text-sm font-medium capitalize', tone)} data-testid={testId}>
      {status || 'unknown'}
    </span>
  );
}

function SystemMonitorContent() {
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [version, setVersion] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logSource, setLogSource] = useState('');
  const [logSearch, setLogSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async (source = logSource, search = logSearch) => {
    const [h, m, v, l] = await Promise.all([
      fetchSystemHealth(),
      fetchSystemMetrics(),
      fetchSystemVersion(),
      fetchSystemLogs({ source: source || undefined, action: search || undefined, limit: 50 }),
    ]);
    setHealth(h);
    setMetrics(m);
    setVersion(v);
    setLogs(l.logs || []);
  };

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, []);

  const config = useMemo(() => metrics ? {
    database: metrics.database?.provider,
    workers: metrics.database ? `${metrics.database.provider}` : '—',
  } : null, [metrics]);

  if (loading) {
    return <LoadingState message="Loading system monitor…" testId="system-monitor-loading" />;
  }

  const storage = metrics?.storage;
  const jobs = metrics?.jobs;
  const sessions = metrics?.audit_sessions;
  const users = metrics?.users;
  const performance = metrics?.performance;
  const backup = metrics?.backup;
  const database = metrics?.database;

  return (
    <DashboardLayout testId="system-monitor-layout">
      <PageHeader
        title="System Monitor"
        description="Production operations dashboard — health, jobs, sessions, users, and logs."
        testId="system-monitor-header"
      />

      <section data-testid="system-health-cards">
        <ContentCard title="System Health" testId="system-health-panel">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Application" value={<StatusBadge status={health?.application} testId="health-application" />} testId="health-card-application" />
            <MetricCard label="Database" value={<StatusBadge status={health?.database} testId="health-database" />} testId="health-card-database" />
            <MetricCard label="Workers" value={<StatusBadge status={health?.workers} testId="health-workers" />} testId="health-card-workers" />
            <MetricCard label="Job Queue" value={<StatusBadge status={health?.job_queue} testId="health-job-queue" />} testId="health-card-job-queue" />
            <MetricCard label="Disk" value={<StatusBadge status={health?.disk} testId="health-disk" />} testId="health-card-disk" />
            <MetricCard label="Memory" value={<StatusBadge status={health?.memory} testId="health-memory" />} testId="health-card-memory" />
            <MetricCard label="CPU" value={<StatusBadge status={health?.cpu} testId="health-cpu" />} testId="health-card-cpu" />
            <MetricCard label="Overall" value={<StatusBadge status={health?.status} testId="health-overall" />} testId="health-card-overall" />
          </div>
          <div className="grid gap-3 sm:grid-cols-3 mt-4">
            <MetricCard label="Version" value={version?.version} testId="health-version" />
            <MetricCard label="Uptime" value={formatUptime(health?.uptime_seconds)} testId="health-uptime" />
            <MetricCard label="Environment" value={version?.environment} testId="health-environment" />
          </div>
        </ContentCard>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <ContentCard title="Database" testId="system-database-panel">
          <dl className="text-sm space-y-2">
            <div className="flex justify-between"><dt>Provider</dt><dd data-testid="db-provider">{database?.provider}</dd></div>
            <div className="flex justify-between"><dt>Connection</dt><dd data-testid="db-connection">{database?.connected ? 'Connected' : 'Disconnected'}</dd></div>
            <div className="flex justify-between"><dt>Pool usage</dt><dd data-testid="db-pool">{database?.pool_checked_out}/{database?.pool_size}</dd></div>
            <div className="flex justify-between"><dt>Migration</dt><dd data-testid="db-migration">{database?.migration_version || '—'}</dd></div>
            <div className="flex justify-between"><dt>Database size</dt><dd data-testid="db-size">{formatBytes(database?.database_size_bytes)}</dd></div>
          </dl>
        </ContentCard>

        <ContentCard title="Job Monitor" testId="system-jobs-panel">
          <div className="grid grid-cols-3 gap-2 mb-3">
            <MetricCard label="Queued" value={jobs?.queued} testId="jobs-queued" />
            <MetricCard label="Running" value={jobs?.running} testId="jobs-running" />
            <MetricCard label="Completed" value={jobs?.completed} testId="jobs-completed" />
            <MetricCard label="Failed" value={jobs?.failed} testId="jobs-failed" />
            <MetricCard label="Retrying" value={jobs?.retrying} testId="jobs-retrying" />
            <MetricCard label="Cancelled" value={jobs?.cancelled} testId="jobs-cancelled" />
          </div>
          <dl className="text-sm space-y-1">
            <div className="flex justify-between"><dt>Avg duration</dt><dd data-testid="jobs-avg-duration">{formatDuration(jobs?.average_duration_seconds)}</dd></div>
            <div className="flex justify-between"><dt>Worker utilization</dt><dd data-testid="jobs-worker-util">{jobs?.worker_utilization_percent ?? 0}%</dd></div>
            <div className="flex justify-between"><dt>Oldest job</dt><dd className="truncate max-w-[12rem]" data-testid="jobs-oldest">{jobs?.oldest_job_at?.slice(0, 19) || '—'}</dd></div>
          </dl>
        </ContentCard>

        <ContentCard title="Audit Sessions" testId="system-sessions-panel">
          <div className="grid grid-cols-2 gap-2">
            <MetricCard label="Total" value={sessions?.total_sessions} testId="sessions-total" />
            <MetricCard label="Open" value={sessions?.open_sessions} testId="sessions-open" />
            <MetricCard label="Completed" value={sessions?.completed_audits} testId="sessions-completed" />
            <MetricCard label="Archived" value={sessions?.archived_audits} testId="sessions-archived" />
          </div>
          <p className={cn(theme.text.label, 'mt-3')} data-testid="sessions-avg-duration">
            Avg audit duration: {sessions?.average_audit_duration_hours != null ? `${sessions.average_audit_duration_hours}h` : '—'}
          </p>
        </ContentCard>

        <ContentCard title="Users & Sessions" testId="system-users-panel">
          <div className="grid grid-cols-2 gap-2">
            <MetricCard label="Active users" value={users?.active_users} testId="users-active" />
            <MetricCard label="Logged in" value={users?.logged_in_users} testId="users-logged-in" />
            <MetricCard label="Failed logins (24h)" value={users?.failed_logins_24h} testId="users-failed-logins" />
            <MetricCard label="Concurrent sessions" value={users?.concurrent_sessions} testId="users-concurrent-sessions" />
          </div>
          <p className={cn(theme.text.label, 'mt-3')} data-testid="users-last-login">
            Last login: {users?.last_login_at?.slice(0, 19) || '—'}
          </p>
        </ContentCard>

        <ContentCard title="Performance" testId="system-performance-panel">
          <dl className="text-sm space-y-2">
            <div className="flex justify-between"><dt>Avg merge</dt><dd data-testid="perf-merge">{formatDuration(performance?.average_merge_seconds)}</dd></div>
            <div className="flex justify-between"><dt>Avg comparison</dt><dd data-testid="perf-comparison">{formatDuration(performance?.average_comparison_seconds)}</dd></div>
            <div className="flex justify-between"><dt>Avg report</dt><dd data-testid="perf-report">{formatDuration(performance?.average_report_seconds)}</dd></div>
            <div className="flex justify-between"><dt>Largest workbook</dt><dd data-testid="perf-largest-workbook">{formatBytes(performance?.largest_workbook_bytes)}</dd></div>
            <div className="flex justify-between"><dt>Avg workbook size</dt><dd data-testid="perf-avg-workbook">{formatBytes(performance?.average_workbook_bytes)}</dd></div>
          </dl>
        </ContentCard>

        <ContentCard title="Storage & Host" testId="system-storage-panel">
          <dl className="text-sm space-y-2">
            <div className="flex justify-between"><dt>Disk used</dt><dd data-testid="storage-disk-used">{formatBytes(storage?.disk_used_bytes)} ({storage?.disk_used_percent}%)</dd></div>
            <div className="flex justify-between"><dt>Disk free</dt><dd data-testid="storage-disk-free">{formatBytes(storage?.disk_free_bytes)}</dd></div>
            <div className="flex justify-between"><dt>Memory used</dt><dd data-testid="storage-memory">{storage?.memory_used_percent != null ? `${storage.memory_used_percent}%` : '—'}</dd></div>
            <div className="flex justify-between"><dt>CPU</dt><dd data-testid="storage-cpu">{storage?.cpu_percent != null ? `${storage.cpu_percent}%` : '—'}</dd></div>
          </dl>
        </ContentCard>

        <ContentCard title="Backup" testId="system-backup-panel">
          <dl className="text-sm space-y-2">
            <div className="flex justify-between"><dt>Status</dt><dd data-testid="backup-configured">{backup?.configured ? 'Configured' : 'Not configured'}</dd></div>
            <div className="flex justify-between"><dt>Last backup</dt><dd data-testid="backup-last">{backup?.last_backup_at || '—'}</dd></div>
            <div className="flex justify-between"><dt>Next backup</dt><dd data-testid="backup-next">{backup?.next_backup_at || '—'}</dd></div>
            <div className="flex justify-between"><dt>Backup size</dt><dd data-testid="backup-size">{formatBytes(backup?.backup_size_bytes)}</dd></div>
            <div className="flex justify-between"><dt>Restore point</dt><dd data-testid="backup-restore">{backup?.restore_point || '—'}</dd></div>
          </dl>
        </ContentCard>

        <ContentCard title="Configuration (read-only)" testId="system-config-panel">
          <dl className="text-sm space-y-2">
            <div className="flex justify-between"><dt>Database</dt><dd>{config?.database}</dd></div>
            <div className="flex justify-between"><dt>Build ID</dt><dd data-testid="config-build-id">{version?.build_id}</dd></div>
            <div className="flex justify-between"><dt>Version</dt><dd>{version?.version}</dd></div>
            <div className="flex justify-between"><dt>Environment</dt><dd>{version?.environment}</dd></div>
          </dl>
        </ContentCard>
      </div>

      <ContentCard title="Logs" testId="system-logs-panel">
        <div className="flex flex-wrap gap-2 mb-4">
          <select
            className="rounded-md border border-border bg-background px-3 py-2 text-sm"
            value={logSource}
            onChange={(e) => setLogSource(e.target.value)}
            data-testid="logs-source-filter"
          >
            <option value="">All sources</option>
            <option value="system">System</option>
            <option value="worker">Worker</option>
            <option value="security">Security</option>
            <option value="application">Application</option>
          </select>
          <input
            className="rounded-md border border-border bg-background px-3 py-2 text-sm min-w-[12rem]"
            placeholder="Filter by action…"
            value={logSearch}
            onChange={(e) => setLogSearch(e.target.value)}
            data-testid="logs-search-input"
          />
          <Button
            variant="outline"
            size="sm"
            data-testid="logs-filter-button"
            onClick={() => load(logSource, logSearch)}
          >
            Apply
          </Button>
          <Button
            variant="outline"
            size="sm"
            data-testid="logs-export-button"
            onClick={async () => {
              await exportSystemLogs({ source: logSource || undefined, action: logSearch || undefined });
            }}
          >
            Export
          </Button>
        </div>
        <ul className="text-xs space-y-1 max-h-72 overflow-auto" data-testid="system-logs-list">
          {logs.map((entry, index) => (
            <li key={`${entry.timestamp}-${index}`} className="grid grid-cols-5 gap-2 border-b border-border/30 py-1">
              <span>{entry.timestamp?.slice(0, 19)}</span>
              <span>{entry.source}</span>
              <span>{entry.user || '—'}</span>
              <span>{entry.action}</span>
              <span className="text-muted-foreground truncate">{entry.message}</span>
            </li>
          ))}
          {logs.length === 0 && <li className="text-muted-foreground">No logs match the current filters.</li>}
        </ul>
      </ContentCard>
    </DashboardLayout>
  );
}

export default function SystemMonitorPage() {
  return (
    <ProtectedRoute permission="view_system_monitor">
      <SystemMonitorContent />
    </ProtectedRoute>
  );
}
