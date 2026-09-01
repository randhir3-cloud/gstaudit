import React from 'react';
import AuditBadge from '../badges/AuditBadge';
import ProgressCard from '../cards/ProgressCard';
import ContentCard from '../cards/ContentCard';
import { Icons } from '../../icons';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';

export default function AuditHeader({ dashboard }) {
  const readiness = dashboard?.audit_readiness_percent ?? 0;
  const status = dashboard?.audit_status || 'draft';
  const canStart = dashboard?.can_start_audit;

  return (
    <ContentCard testId="audit-header" noPadding>
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <p className={cn(theme.text.label, 'uppercase tracking-wider font-semibold')}>Dealer</p>
          <h2 className={cn(theme.text.heading, 'mt-1')}>
            {dashboard?.dealer_name || 'No dealer loaded'}
          </h2>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
            <Field label="GSTIN" value={dashboard?.gstin} mono />
            <Field label="Trade Name" value={dashboard?.trade_name} />
            <Field label="Financial Year" value={dashboard?.financial_year} />
          </div>
        </div>
        <div className="flex flex-col items-start lg:items-end gap-3 min-w-[200px]">
          <AuditBadge status={status} />
          <div className="w-full lg:w-48">
            <ProgressCard label="Audit Readiness" value={readiness} testId="audit-readiness-bar" />
          </div>
          <div className="flex items-center gap-2 text-sm">
            {canStart ? (
              <>
                <Icons.Check className={cn(Icons.size.sm, 'text-success')} />
                <span className="text-success">Audit can start</span>
              </>
            ) : (
              <>
                <Icons.Alert className={cn(Icons.size.sm, 'text-warning')} />
                <span className="text-warning">More data required</span>
              </>
            )}
            <Icons.Shield className={cn(Icons.size.sm, 'text-muted-foreground ml-1')} />
          </div>
        </div>
      </div>
    </ContentCard>
  );
}

function Field({ label, value, mono }) {
  return (
    <div>
      <p className={theme.text.label}>{label}</p>
      <p className={cn(mono ? theme.text.mono : 'font-medium', 'text-foreground')}>{value || '—'}</p>
    </div>
  );
}
