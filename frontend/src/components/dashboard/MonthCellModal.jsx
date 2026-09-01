import React, { useEffect, useRef } from 'react';
import { formatCount, formatDate } from '../../utils/formatNumbers';
import { DATASET_LABELS } from '../../types/auditSession';
import { Icons } from '../../icons';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';
import { Button } from '../ui/button';

const STATUS_ICON = { uploaded: '✓', missing: '✗', duplicate: '⚠', processing: '⏳' };

export default function MonthCellModal({ cell, datasetKey, gstin, onClose, onResolve }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    dialogRef.current?.focus();
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!cell) return null;

  const isMissing = cell.status === 'missing';
  const isDuplicate = cell.status === 'duplicate';

  return (
    <div
      className="fixed inset-0 z-modal flex items-end sm:items-center justify-center bg-black/50 p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="month-cell-modal-title"
      onClick={onClose}
      onKeyDown={(e) => { if (e.key === 'Escape') onClose(); }}
      data-testid="modal-backdrop"
    >
      <div
        ref={dialogRef}
        tabIndex={-1}
        className={cn(theme.card.shell, 'w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl shadow-xl max-h-[90vh] overflow-y-auto')}
        onClick={(e) => e.stopPropagation()}
        data-testid="month-cell-modal"
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 id="month-cell-modal-title" className={theme.text.subheading}>
              {cell.month}
            </h3>
            <p className={theme.text.muted}>{STATUS_ICON[cell.status]} {cell.status}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close dialog">
            <Icons.Close className={Icons.size.md} />
          </Button>
        </div>

        {isMissing ? (
          <p className={theme.text.muted}>No file uploaded.</p>
        ) : (
          <dl className="space-y-3 text-sm">
            <Row label="Dataset" value={DATASET_LABELS[datasetKey] || datasetKey} />
            <Row label="Filename" value={cell.filenames?.[0] || '—'} mono />
            {cell.filenames?.length > 1 && (
              <div>
                <dt className={theme.text.label}>All Files</dt>
                <dd className={cn(theme.text.mono, 'space-y-1')}>{cell.filenames.map((f) => <p key={f}>{f}</p>)}</dd>
              </div>
            )}
            <Row label="Rows Imported" value={formatCount(cell.row_count)} />
            <Row label="Duplicate Records" value={formatCount(cell.duplicate_rows)} />
            <Row label="Unique Records" value={formatCount(cell.unique_rows)} />
            <Row label="Upload Time" value={formatDate(cell.upload_time)} />
            <Row label="Dealer GSTIN" value={gstin || '—'} mono />
            <Row label="Merge Status" value={cell.merge_status || 'Pending'} />
          </dl>
        )}

        {isDuplicate && onResolve && (
          <div className="mt-5 pt-4 border-t border-border">
            <p className={cn(theme.text.label, 'font-semibold text-warning mb-2')}>Resolve Duplicate</p>
            <div className="flex flex-wrap gap-2">
              {['keep_latest', 'replace', 'delete'].map((action) => (
                <Button
                  key={action}
                  variant="secondary"
                  size="sm"
                  data-testid={`modal-dup-action-${datasetKey}-${action}`}
                  onClick={() => { onResolve(datasetKey, cell.month, action, cell.filenames?.[cell.filenames.length - 1]); onClose(); }}
                  className="capitalize text-xs"
                >
                  {action.replace('_', ' ')}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value, mono }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className={theme.text.label}>{label}</dt>
      <dd className={cn('font-medium text-right text-foreground', mono && theme.text.mono)}>{value}</dd>
    </div>
  );
}
