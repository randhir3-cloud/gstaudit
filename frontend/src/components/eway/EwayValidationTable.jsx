import React from 'react';

const STATUS_STYLES = {
  valid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
  wrong_section: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  unknown: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300',
  pending_dealer_gstin: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
};

export default function EwayValidationTable({ files }) {
  if (!files.length) return null;

  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden shadow-sm" data-testid="eway-validation-table">
      <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800">
        <h3 className="font-bold text-zinc-900 dark:text-zinc-50">Upload Validation</h3>
        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
          Classification is based on Excel content — not the selected tab.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-zinc-50 dark:bg-zinc-950 text-left">
            <tr>
              {['Filename', 'Detected Type', 'Confidence', 'Dealer GSTIN', 'Month', 'Financial Year', 'Status'].map((h) => (
                <th key={h} className="px-4 py-3 font-semibold text-zinc-600 dark:text-zinc-300 whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {files.map((entry) => {
              const c = entry.classification || {};
              return (
                <tr key={entry.id} className="border-t border-zinc-100 dark:border-zinc-800">
                  <td className="px-4 py-3 text-zinc-800 dark:text-zinc-200 max-w-[200px] truncate" title={entry.name}>{entry.name}</td>
                  <td className="px-4 py-3 uppercase font-medium">{c.detected_type || '—'}</td>
                  <td className="px-4 py-3">{c.confidence != null ? `${c.confidence}%` : '—'}</td>
                  <td className="px-4 py-3 font-mono text-xs">{c.dealer_gstin || '—'}</td>
                  <td className="px-4 py-3">{c.month || entry.period || '—'}</td>
                  <td className="px-4 py-3">{c.financial_year || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${STATUS_STYLES[c.status] || STATUS_STYLES.unknown}`}>
                      {(c.status || 'unknown').replace(/_/g, ' ')}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
