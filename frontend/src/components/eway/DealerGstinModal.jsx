import React, { useState } from 'react';
import { Building2 } from 'lucide-react';

export default function DealerGstinModal({ isOpen, onSubmit, onCancel }) {
  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const gstin = value.trim().toUpperCase();
    if (!/^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]$/.test(gstin)) {
      setError('Enter a valid 15-character GSTIN.');
      return;
    }
    onSubmit(gstin);
    setValue('');
    setError('');
  };

  return (
    <div className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" data-testid="dealer-gstin-modal">
      <form onSubmit={handleSubmit} className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-blue-600 text-white"><Building2 className="h-5 w-5" /></div>
          <div>
            <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">Dealer GSTIN Required</h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Needed once to classify E-Way Bills automatically.</p>
          </div>
        </div>
        <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">Dealer GSTIN</label>
        <input
          data-testid="dealer-gstin-input"
          value={value}
          onChange={(e) => { setValue(e.target.value); setError(''); }}
          placeholder="03AABCU9603R1ZX"
          className="mt-2 w-full rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-3 text-sm font-mono"
        />
        {error && <p className="text-sm text-rose-600 mt-2">{error}</p>}
        <div className="flex gap-3 mt-6">
          <button type="button" onClick={onCancel} className="flex-1 py-2.5 rounded-xl bg-zinc-100 dark:bg-zinc-800 text-sm font-medium">Cancel</button>
          <button type="submit" data-testid="dealer-gstin-submit" className="flex-1 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-medium">Save GSTIN</button>
        </div>
      </form>
    </div>
  );
}
