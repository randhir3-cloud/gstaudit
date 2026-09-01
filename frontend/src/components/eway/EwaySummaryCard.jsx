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
  const monthsUploaded = summary?.uploaded_months?.length ?? files.length;
  const totalRows = summary?.row_count ?? '—';

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
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <Stat label="Dealer Name" value={dealerName !== 'No dealer loaded' ? dealerName : '—'} />
        <Stat label="GSTIN" value={dealerMetadata?.gstin} />
        <Stat label="Financial Year" value={summary?.financial_year || dealerMetadata?.financial_year} />
        <Stat label="Months Uploaded" value={monthsUploaded} />
        <Stat label="Total Rows" value={totalRows} />
      </div>
    </div>
  );
}
