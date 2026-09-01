import React from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../cards/ContentCard';
import StatusBadge from '../common/StatusBadge';
import { Button } from '../ui/button';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';
import { Icons } from '../../icons';

function formatEta(seconds) {
  if (seconds == null) return '';
  if (seconds < 60) return `${seconds}s remaining`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s remaining`;
}

function JobRow({ job, onCancel, onRetry }) {
  const p = job.progress || {};
  const isActive = job.status === 'running' || job.status === 'queued' || job.status === 'retrying';

  return (
    <li
      className={cn(theme.card.shell, 'p-3 space-y-2')}
      data-testid={`job-row-${job.job_id}`}
      data-job-status={job.status}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className={cn(theme.text.body, 'font-medium')}>{job.title || job.job_type}</p>
          <p className={theme.text.label}>{job.job_type}</p>
        </div>
        <StatusBadge status={job.status} label={job.status} testId={`job-status-${job.job_id}`} />
      </div>

      {isActive && (
        <div data-testid={`job-progress-${job.job_id}`}>
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>{p.stage || 'Starting…'}</span>
            <span>{p.percent ?? 0}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div className="h-full bg-primary transition-all" style={{ width: `${p.percent ?? 0}%` }} data-testid={`job-progress-bar-${job.job_id}`} />
          </div>
          {(p.rows_total > 0 || p.eta_seconds != null) && (
            <p className={cn(theme.text.label, 'mt-1')} data-testid={`job-progress-detail-${job.job_id}`}>
              {p.rows_total > 0 && `${(p.rows_processed ?? 0).toLocaleString()} / ${p.rows_total.toLocaleString()}`}
              {p.eta_seconds != null && ` · ${formatEta(p.eta_seconds)}`}
            </p>
          )}
        </div>
      )}

      {job.error && <p className={cn(theme.text.label, 'text-danger')}>{job.error}</p>}

      <div className="flex flex-wrap gap-2">
        {isActive && (
          <Button type="button" variant="outline" size="sm" onClick={() => onCancel(job.job_id)} data-testid={`job-cancel-${job.job_id}`}>
            Cancel
          </Button>
        )}
        {(job.status === 'failed' || job.status === 'cancelled') && (
          <Button type="button" variant="secondary" size="sm" onClick={() => onRetry(job.job_id)} data-testid={`job-retry-${job.job_id}`}>
            Retry
          </Button>
        )}
        {job.status === 'completed' && job.job_type === 'comparison' && (
          <Button variant="link" size="sm" asChild>
            <Link to="/comparison" data-testid={`job-open-comparison-${job.job_id}`}>Open Result</Link>
          </Button>
        )}
        {job.status === 'completed' && job.job_type === 'report' && job.result_ref?.report_id && (
          <Button variant="link" size="sm" asChild>
            <a href={`/audit-report?job=${job.job_id}`} data-testid={`job-open-report-${job.job_id}`}>Open Result</a>
          </Button>
        )}
      </div>
    </li>
  );
}

function JobSection({ title, items, emptyLabel, onCancel, onRetry }) {
  if (!items.length) return null;
  return (
    <div className="space-y-2" data-testid={`job-section-${title.toLowerCase()}`}>
      <h4 className={cn(theme.text.sectionTitle, 'text-sm flex items-center gap-2')}>
        {title}
        <span className={theme.text.label}>({items.length})</span>
      </h4>
      <ul className="space-y-2">{items.map((job) => <JobRow key={job.job_id} job={job} onCancel={onCancel} onRetry={onRetry} />)}</ul>
    </div>
  );
}

export default function JobQueuePanel({ jobs, grouped, onCancel, onRetry, loading }) {
  const total = jobs.length;

  return (
    <ContentCard testId="job-queue-panel" title="Job Queue" description="Background processing for merge, comparison, intelligence, and reports.">
      {loading && total === 0 && (
        <p className={cn(theme.text.muted, 'flex items-center gap-2')}>
          <Icons.Loading className={cn(Icons.size.sm, 'animate-spin')} aria-hidden /> Loading jobs…
        </p>
      )}
      {!loading && total === 0 && (
        <p className={theme.text.muted} data-testid="job-queue-empty">No background jobs for this session.</p>
      )}
      <div className="space-y-4">
        <JobSection title="Running" items={grouped.running} onCancel={onCancel} onRetry={onRetry} />
        <JobSection title="Queued" items={grouped.queued} onCancel={onCancel} onRetry={onRetry} />
        <JobSection title="Completed" items={grouped.completed} onCancel={onCancel} onRetry={onRetry} />
        <JobSection title="Failed" items={grouped.failed} onCancel={onCancel} onRetry={onRetry} />
      </div>
    </ContentCard>
  );
}
