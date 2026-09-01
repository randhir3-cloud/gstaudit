import React from 'react';
import { FileSpreadsheet, Trash2, ArrowUp, ArrowDown } from 'lucide-react';
import { formatBytes } from '../../utils/fileHelpers';

export default function FileList({
  files,
  onMoveUp,
  onMoveDown,
  onRemove,
  onClearAll,
  notice,
}) {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <h3 className="font-bold text-zinc-900 dark:text-zinc-50 text-base">Files to Merge</h3>
          <span className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs px-2.5 py-0.5 rounded-full font-bold">
            {files.length}
          </span>
        </div>
        <button
          type="button"
          onClick={onClearAll}
          className="text-xs font-medium text-rose-600 hover:text-rose-700 dark:text-rose-400"
        >
          Clear All
        </button>
      </div>

      {notice && <div className="m-4">{notice}</div>}

      <div className="divide-y divide-zinc-100 dark:divide-zinc-800 max-h-[420px] overflow-y-auto">
        {files.map((fileEntry, index) => (
          <div
            key={fileEntry.id}
            className="px-5 py-3.5 flex items-center justify-between hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30"
          >
            <div className="flex items-center space-x-3.5 overflow-hidden pr-4">
              <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg flex-shrink-0 text-zinc-500 dark:text-zinc-400">
                <FileSpreadsheet className="h-5 w-5" />
              </div>
              <div className="overflow-hidden">
                <h4 className="font-medium text-sm text-zinc-800 dark:text-zinc-100 truncate" title={fileEntry.name}>
                  {fileEntry.name}
                </h4>
                <div className="flex items-center space-x-2 text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  <span>{formatBytes(fileEntry.size)}</span>
                  {fileEntry.period && (
                    <>
                      <span className="h-1 w-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                      <span className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 rounded font-medium text-blue-700 dark:text-blue-300">
                        {fileEntry.period}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-1.5 flex-shrink-0">
              <button type="button" onClick={() => onMoveUp(index)} disabled={index === 0} className="p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30">
                <ArrowUp className="h-4 w-4" />
              </button>
              <button type="button" onClick={() => onMoveDown(index)} disabled={index === files.length - 1} className="p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30">
                <ArrowDown className="h-4 w-4" />
              </button>
              <button type="button" onClick={() => onRemove(fileEntry.id)} className="p-1.5 rounded-md hover:bg-rose-50 dark:hover:bg-rose-950/30 text-rose-500">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
