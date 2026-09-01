import React from 'react';
import { X } from 'lucide-react';

export default function WorkbookPreviewModal({ isOpen, onClose, preview, filename }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl w-full max-w-5xl max-h-[85vh] overflow-hidden flex flex-col">
        <div className="px-5 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">Workbook Preview</h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">{filename}</p>
          </div>
          <button type="button" onClick={onClose} className="p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="overflow-auto p-5 space-y-6">
          {(preview || []).map((sheet) => (
            <div key={sheet.name} className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-zinc-900 dark:text-zinc-100">{sheet.name}</h4>
                <span className="text-xs text-zinc-500">{sheet.row_count} rows</span>
              </div>
              <div className="overflow-x-auto rounded-xl border border-zinc-200 dark:border-zinc-800">
                <table className="min-w-full text-xs">
                  <thead className="bg-zinc-50 dark:bg-zinc-950">
                    <tr>
                      {(sheet.columns || []).map((col) => (
                        <th key={col} className="px-3 py-2 text-left font-semibold text-zinc-600 dark:text-zinc-300 whitespace-nowrap">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(sheet.sample_rows || []).map((row, rowIndex) => (
                      <tr key={rowIndex} className="border-t border-zinc-100 dark:border-zinc-800">
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex} className="px-3 py-2 text-zinc-700 dark:text-zinc-300 whitespace-nowrap">
                            {cell ?? '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
          {(!preview || preview.length === 0) && (
            <p className="text-sm text-zinc-500">No preview available. Merge files first.</p>
          )}
        </div>
      </div>
    </div>
  );
}
