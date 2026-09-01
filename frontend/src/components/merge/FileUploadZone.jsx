import React, { useRef } from 'react';
import { Upload } from 'lucide-react';

export default function FileUploadZone({ onFilesSelected, isDragOver, onDragOver, onDragLeave, onDrop }) {
  const fileInputRef = useRef(null);

  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={() => fileInputRef.current?.click()}
      className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 bg-white dark:bg-zinc-900 ${
        isDragOver
          ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 scale-[0.99] shadow-inner'
          : 'border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 shadow-sm'
      }`}
    >
      <input
        ref={fileInputRef}
        data-testid="eway-file-input"
        type="file"
        multiple
        accept=".xlsx,.xls"
        onChange={(e) => onFilesSelected(Array.from(e.target.files || []))}
        className="hidden"
      />
      <div className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-100 dark:border-zinc-800 mb-4 text-zinc-500 dark:text-zinc-400">
        <Upload className="h-8 w-8 animate-pulse text-blue-500" />
      </div>
      <h3 className="font-semibold text-zinc-800 dark:text-zinc-200">Drag & drop your files here</h3>
      <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-[220px]">
        Supports Excel spreadsheets .xlsx and .xls
      </p>
      <button
        type="button"
        className="mt-5 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl transition-all shadow-md shadow-blue-500/10"
      >
        Browse Files
      </button>
    </div>
  );
}
