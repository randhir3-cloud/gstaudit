import React from 'react';
import { dealerDisplayName } from '../../types/dealer';

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-zinc-500 dark:text-zinc-400 font-semibold">{label}</p>
      <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 mt-0.5">{value ?? '—'}</p>
    </div>
  );
}

const STATUS_LABELS = {
  idle: 'Ready',
  merging: 'Merging…',
  merged: 'Merged',
  error: 'Error',
};

export default function EwaySummaryCard({ workflow, directionLabel }) {
  const { dealerMetadata, summary, mergeStatus, files } = workflow;
  const dealerName = dealerDisplayName(dealerMetadata);

  // Compute unique months
  const uniqueMonthsCount = React.useMemo(() => {
    const months = new Set();
    files.forEach((f) => {
      const m = f.classification?.month || f.period;
      if (m && m !== '—' && m !== 'Unknown Period') {
        months.add(m);
      }
    });
    return months.size;
  }, [files]);

  const gstin = dealerMetadata?.gstin || workflow.files[0]?.classification?.dealer_gstin || '';
  const financialYear = summary?.financial_year || dealerMetadata?.financial_year || workflow.files[0]?.classification?.financial_year || '';
  const totalFiles = files.length;
  const totalRows = summary?.row_count ?? (workflow.files.reduce((acc, f) => acc + (f.classification?.rows_inspected || 0), 0) || '—');

  return (
    <div className="rounded-2xl border border-emerald-200/70 dark:border-emerald-900/40 bg-gradient-to-r from-emerald-50/70 to-white dark:from-emerald-950/20 dark:to-zinc-900 p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="font-bold text-zinc-950 dark:text-white">{directionLabel} E-Way Bill</h3>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Independent workflow — compare with {directionLabel === 'Outward' ? 'GSTR-1' : 'GSTR-2A'} later</p>
        </div>
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
          mergeStatus === 'merged'
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
            : mergeStatus === 'merging'
              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
              : 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300'
        }`}
        >
          {STATUS_LABELS[mergeStatus] || mergeStatus}
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Stat label="Dealer Name" value={dealerName !== 'No dealer loaded' ? dealerName : '—'} />
        <Stat label="GSTIN" value={gstin || '—'} />
        <Stat label="Financial Year" value={financialYear || '—'} />
        <Stat label="Files Uploaded" value={totalFiles} />
        <Stat label="Unique Months" value={uniqueMonthsCount > 0 ? uniqueMonthsCount : (totalFiles > 0 ? '—' : 0)} />
        <Stat label="Total Rows" value={totalRows} />
      </div>
    </div>
  );
}
