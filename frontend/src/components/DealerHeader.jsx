import React from 'react';
import { Building2 } from 'lucide-react';
import { useDealer } from '../context/DealerContext';
import { dealerDisplayName } from '../types/dealer';

function MetaItem({ label, value }) {
  return (
    <div className="min-w-[140px]">
      <p className="text-[11px] uppercase tracking-wide text-zinc-500 dark:text-zinc-400 font-semibold">
        {label}
      </p>
      <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 mt-0.5 break-words">
        {value || '—'}
      </p>
    </div>
  );
}

export function DealerHeaderView({
  dealer,
  currentDataset = '',
  compact = false,
  className = '',
}) {
  const hasDealer = Boolean(dealer?.gstin);

  if (!hasDealer) {
    return (
      <div
        className={`rounded-2xl border border-dashed border-zinc-300 dark:border-zinc-700 bg-zinc-50/80 dark:bg-zinc-900/40 p-4 text-sm text-zinc-500 dark:text-zinc-400 ${className}`}
      >
        Upload GSTR-1 or GSTR-2A files to load dealer metadata from the Read me sheet.
      </div>
    );
  }

  return (
    <div
      className={`rounded-2xl border border-blue-200/70 dark:border-blue-900/40 bg-gradient-to-r from-blue-50/80 to-white dark:from-blue-950/20 dark:to-zinc-900 shadow-sm ${compact ? 'p-4' : 'p-5'} ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-xl bg-blue-600 text-white shrink-0">
          <Building2 className="h-5 w-5" />
        </div>
        <div className="flex-1 space-y-3">
          <div>
            <h2 className={`font-bold text-zinc-950 dark:text-white ${compact ? 'text-base' : 'text-lg'}`}>
              {dealerDisplayName(dealer)}
            </h2>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">Dealer Information</p>
          </div>
          <div className={`grid gap-4 ${compact ? 'grid-cols-2 md:grid-cols-3' : 'grid-cols-2 md:grid-cols-3 lg:grid-cols-5'}`}>
            <MetaItem label="GSTIN" value={dealer.gstin} />
            <MetaItem label="Financial Year" value={dealer.financial_year} />
            <MetaItem label="Tax Period" value={dealer.tax_period} />
            <MetaItem label="Current Dataset" value={currentDataset} />
            {!compact && (
              <MetaItem label="Trade Name" value={dealer.trade_name || dealer.legal_name} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DealerHeader(props) {
  const context = useDealer();
  return (
    <DealerHeaderView
      dealer={props.dealer || context.dealer}
      currentDataset={props.currentDataset ?? context.currentDataset}
      compact={props.compact}
      className={props.className}
    />
  );
}
