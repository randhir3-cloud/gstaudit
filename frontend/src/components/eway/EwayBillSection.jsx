import React from 'react';
import { ArrowDownLeft, ArrowUpRight } from 'lucide-react';
import { useEway } from '../../context/EwayContext';
import EwayWorkflowPanel from './EwayWorkflowPanel';

export default function EwayBillSection() {
  const { activeSubTab, setActiveSubTab } = useEway();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">E-Way Bill Workflows</h3>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
          Outward and Inward are independent. Files are auto-classified from Excel content — never from the selected tab alone.
        </p>
      </div>

      <div className="grid grid-cols-2 p-1 bg-zinc-100 dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 max-w-md">
        <button
          type="button"
          data-testid="eway-tab-outward"
          onClick={() => setActiveSubTab('outward')}
          className={`py-2 px-4 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2 ${
            activeSubTab === 'outward'
              ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-blue-400 shadow-sm border border-zinc-200/50 dark:border-zinc-700/50'
              : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          }`}
        >
          <ArrowUpRight className="h-4 w-4" />
          Outward
        </button>
        <button
          type="button"
          data-testid="eway-tab-inward"
          onClick={() => setActiveSubTab('inward')}
          className={`py-2 px-4 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2 ${
            activeSubTab === 'inward'
              ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-blue-400 shadow-sm border border-zinc-200/50 dark:border-zinc-700/50'
              : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
          }`}
        >
          <ArrowDownLeft className="h-4 w-4" />
          Inward
        </button>
      </div>

      {activeSubTab === 'outward' ? (
        <EwayWorkflowPanel direction="outward" directionLabel="Outward" />
      ) : (
        <EwayWorkflowPanel direction="inward" directionLabel="Inward" />
      )}
    </div>
  );
}
