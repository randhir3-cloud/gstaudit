import React from 'react';
import { FileSpreadsheet, Trash2, ArrowUp, ArrowDown, HelpCircle } from 'lucide-react';
import { formatBytes } from '../../utils/fileHelpers';

const STATUS_BADGES = {
  valid: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-200/50 dark:border-emerald-800/50',
  wrong_section: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200/50 dark:border-amber-800/50',
  unknown: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300 border-rose-200/50 dark:border-rose-800/50',
  pending_dealer_gstin: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border-zinc-200/50 dark:border-zinc-700/50',
  processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200/50 dark:border-blue-800/50',
  previously_merged: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300 border-purple-200/60 dark:border-purple-800/60 font-semibold',
  duplicate_file: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300 border-orange-200/60 dark:border-orange-800/60 font-semibold',
  contains_duplicate_records: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200/50 dark:border-amber-800/50',
};

const TYPE_BADGES = {
  inward: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800/40',
  outward: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border-purple-200 dark:border-purple-800/40',
};

export default function UnifiedMergeFileList({
  files = [],
  mode = 'gstr', // 'gstr' | 'eway'
  onMoveUp,
  onMoveDown,
  onRemove,
  onClearAll,
  notice,
}) {
  if (!files || files.length === 0) return null;

  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden" data-testid="unified-merge-file-list">
      {/* Header with Title, Count Badge, and Clear All */}
      <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-900/60 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <h3 className="font-bold text-zinc-900 dark:text-zinc-50 text-base">Files to Merge</h3>
          <span className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs px-2.5 py-0.5 rounded-full font-bold">
            {files.length}
          </span>
        </div>
        <button
          type="button"
          onClick={onClearAll}
          className="text-xs font-semibold text-rose-600 hover:text-rose-700 dark:text-rose-400 hover:underline transition-colors"
        >
          Clear All
        </button>
      </div>

      {/* Info notice if provided */}
      {notice && (
        <div className="p-3.5 bg-blue-50/50 dark:bg-blue-950/20 border-b border-blue-100/50 dark:border-blue-900/30 text-xs text-zinc-600 dark:text-zinc-300 flex items-start gap-2.5">
          <HelpCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
          <div>{notice}</div>
        </div>
      )}

      {/* Constrained Scrollable List Container (400-500px max height) */}
      <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80 max-h-[460px] overflow-y-auto">
        {files.map((fileEntry, index) => {
          const c = fileEntry.classification || {};
          const detectedType = c.detected_type || (mode === 'eway' ? '—' : '');
          const confidence = c.confidence != null ? `${c.confidence}%` : '';
          const dealerGstin = c.dealer_gstin || '';
          const period = c.month || fileEntry.period || '—';
          const fy = c.financial_year || '';
          const status = fileEntry.status || c.status || 'valid';
          const isExcluded = status === 'previously_merged' || status === 'duplicate_file';

          return (
            <div
              key={fileEntry.id}
              className={`px-5 py-3.5 flex items-center justify-between hover:bg-zinc-50/60 dark:hover:bg-zinc-800/40 transition-colors gap-3 ${
                isExcluded ? 'bg-zinc-50/40 dark:bg-zinc-900/40 opacity-80' : ''
              }`}
            >
              {/* File details */}
              <div className="flex items-center space-x-3.5 min-w-0 flex-1">
                <div className={`p-2.5 rounded-xl flex-shrink-0 border ${
                  isExcluded
                    ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200/50 dark:border-amber-800/50'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 border-zinc-200/50 dark:border-zinc-700/50'
                }`}>
                  <FileSpreadsheet className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>

                <div className="min-w-0 flex-1">
                  {/* Row 1: Filename and Badges */}
                  <div className="flex items-center flex-wrap gap-2">
                    <h4
                      className="font-medium text-sm text-zinc-900 dark:text-zinc-100 truncate max-w-xs md:max-w-md"
                      title={fileEntry.name}
                    >
                      {fileEntry.name}
                    </h4>

                    {mode === 'eway' && detectedType && (
                      <span
                        className={`text-[11px] uppercase font-bold px-2 py-0.5 rounded-md border ${
                          TYPE_BADGES[detectedType.toLowerCase()] || 'bg-zinc-100 text-zinc-700'
                        }`}
                      >
                        {detectedType.toUpperCase()}
                      </span>
                    )}

                    {mode === 'eway' && confidence && (
                      <span className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800/60 px-1.5 py-0.5 rounded">
                        {confidence}
                      </span>
                    )}

                    {status && (
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                          STATUS_BADGES[status] || STATUS_BADGES.unknown
                        }`}
                      >
                        {status === 'previously_merged'
                          ? 'Previously Merged'
                          : status === 'duplicate_file'
                          ? 'Duplicate File'
                          : status.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>

                  {/* Row 2: Metadata tags */}
                  <div className="flex items-center flex-wrap gap-x-3 gap-y-1 text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                    {mode === 'eway' && dealerGstin && (
                      <span className="font-mono text-[11px] bg-zinc-100 dark:bg-zinc-800/80 px-1.5 py-0.5 rounded text-zinc-700 dark:text-zinc-300">
                        {dealerGstin}
                      </span>
                    )}
                    {period && period !== '—' && (
                      <span className="font-medium text-zinc-700 dark:text-zinc-300">
                        Period: {period}
                      </span>
                    )}
                    {fy && (
                      <span>
                        FY: <strong className="font-medium text-zinc-700 dark:text-zinc-300">{fy}</strong>
                      </span>
                    )}
                    {fileEntry.duplicateOf && (
                      <span className="text-orange-600 dark:text-orange-400 font-medium">
                        Duplicate of: {fileEntry.duplicateOf}
                      </span>
                    )}
                    {c.duplicate_of && (
                      <span className="text-orange-600 dark:text-orange-400 font-medium">
                        Duplicate of: {c.duplicate_of}
                      </span>
                    )}
                    {fileEntry.previouslyMergedReason && (
                      <span className="text-purple-600 dark:text-purple-400 font-medium">
                        {fileEntry.previouslyMergedReason}
                      </span>
                    )}
                    <span>{formatBytes(fileEntry.size)}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons: Move Up, Move Down, Delete */}
              <div className="flex items-center space-x-1 flex-shrink-0">
                <button
                  type="button"
                  onClick={() => onMoveUp(index)}
                  disabled={index === 0 || isExcluded}
                  aria-label={`Move ${fileEntry.name} up`}
                  title="Move Up"
                  className="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
                >
                  <ArrowUp className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => onMoveDown(index)}
                  disabled={index === files.length - 1 || isExcluded}
                  aria-label={`Move ${fileEntry.name} down`}
                  title="Move Down"
                  className="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
                >
                  <ArrowDown className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(fileEntry.id)}
                  aria-label={`Remove ${fileEntry.name}`}
                  title="Remove file"
                  className="p-1.5 rounded-lg text-rose-500 hover:text-rose-700 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
