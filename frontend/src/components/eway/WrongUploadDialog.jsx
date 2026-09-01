import React from 'react';
import { ArrowLeftRight } from 'lucide-react';

export default function WrongUploadDialog({ isOpen, detectedType, targetDirection, filename, onMove, onCancel }) {
  if (!isOpen) return null;

  const label = detectedType?.toUpperCase() || 'UNKNOWN';

  return (
    <div className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" data-testid="wrong-upload-dialog">
      <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center gap-3 text-amber-600 mb-4">
          <ArrowLeftRight className="h-6 w-6" />
          <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">Wrong Section Detected</h3>
        </div>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
          <strong>{filename}</strong> has been detected as an <strong>{label}</strong> E-Way Bill.
        </p>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-6">
          Would you like to move it to the <strong>{targetDirection?.toUpperCase()}</strong> section?
        </p>
        <div className="flex gap-3">
          <button type="button" data-testid="wrong-upload-cancel" onClick={onCancel} className="flex-1 py-2.5 rounded-xl bg-zinc-100 dark:bg-zinc-800 text-sm font-medium">Cancel</button>
          <button type="button" data-testid="wrong-upload-move" onClick={onMove} className="flex-1 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-medium">Move Automatically</button>
        </div>
      </div>
    </div>
  );
}
