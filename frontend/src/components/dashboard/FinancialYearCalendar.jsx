import React, { useMemo, useState, useCallback } from 'react';
import { DATASET_LABELS } from '../../types/auditSession';
import { formatCount, shortDatasetLabel } from '../../utils/formatNumbers';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';
import StatusTooltip from './StatusTooltip';
import MonthCellModal from './MonthCellModal';

const STATUS_ICON = { uploaded: '✓', missing: '✗', duplicate: '⚠', processing: '⏳' };

function MonthCell({ cell, datasetKey, onClick }) {
  const icon = STATUS_ICON[cell.status] || '✗';
  const style = theme.calendar.cellStatus[cell.status] || theme.calendar.cellStatus.missing;

  const tooltipLines = [];
  if (cell.status === 'uploaded' || cell.status === 'duplicate' || cell.status === 'processing') {
    if (cell.row_count) tooltipLines.push(`Rows: ${formatCount(cell.row_count)}`);
    if (cell.duplicate_rows) tooltipLines.push(`Duplicates: ${formatCount(cell.duplicate_rows)}`);
    if (cell.filenames?.[0]) tooltipLines.push(`Filename: ${cell.filenames[0]}`);
    if (cell.upload_time) tooltipLines.push(`Upload: ${cell.upload_time.slice(0, 10)}`);
  }

  return (
    <button
      type="button"
      onClick={() => onClick(cell, datasetKey)}
      className={cn(theme.calendar.monthCell, style)}
      data-testid={`month-cell-${datasetKey}-${cell.short}`}
      aria-label={`${cell.month} ${DATASET_LABELS[datasetKey]}: ${cell.status}`}
    >
      <StatusTooltip title={`${icon} ${cell.status}`} details={tooltipLines}>
        <span className="block text-base leading-none" aria-hidden>{icon}</span>
      </StatusTooltip>
      {cell.status === 'missing' ? (
        <span className={cn('block text-[10px] sm:text-xs mt-1 font-medium', theme.text.muted)}>Missing</span>
      ) : cell.status === 'processing' ? (
        <span className={cn('block text-[10px] sm:text-xs mt-1 font-medium', theme.text.muted)}>Processing</span>
      ) : (
        <>
          <span className="block text-[10px] sm:text-xs mt-1 font-semibold tabular-nums">{formatCount(cell.row_count)}</span>
          {cell.duplicate_rows > 0 && (
            <span className="block text-[9px] sm:text-[10px] text-warning">Dup {formatCount(cell.duplicate_rows)}</span>
          )}
        </>
      )}
    </button>
  );
}

export default function FinancialYearCalendar({ monthCoverage, datasetKeys, gstin, onResolveDuplicate }) {
  const [modal, setModal] = useState(null);

  const keys = datasetKeys?.length ? datasetKeys : Object.keys(monthCoverage || {});

  const rows = useMemo(() => {
    const first = keys.find((k) => monthCoverage?.[k]?.months?.length);
    if (!first) return [];
    return monthCoverage[first].months.map((m, idx) => ({
      month: m.month,
      short: m.short,
      cells: keys.map((k) => monthCoverage[k]?.months?.[idx] || { ...m, status: 'missing', uploaded: false, row_count: 0 }),
    }));
  }, [monthCoverage, keys]);

  const handleCellClick = useCallback((cell, datasetKey) => {
    setModal({ cell, datasetKey });
  }, []);

  if (!rows.length) return null;

  return (
    <>
      <div className={theme.calendar.shell} data-testid="fy-calendar">
        <div className="overflow-x-auto max-w-full">
          <div className="inline-block min-w-full align-middle">
            <table className={cn(theme.table.base, 'border-collapse')} role="grid" aria-label="Financial year month coverage">
              <thead>
                <tr className={theme.table.head}>
                  <th scope="col" className={cn(theme.calendar.headerCell, 'left-0 z-20 min-w-[64px]')}>
                    Month
                  </th>
                  {keys.map((key) => (
                    <th
                      key={key}
                      scope="col"
                      className={cn(theme.calendar.headerCell, 'top-0 z-10 text-center whitespace-nowrap border-r-0')}
                      data-testid={`calendar-header-${key}`}
                    >
                      {shortDatasetLabel(key, DATASET_LABELS)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.short} className="border-b border-border last:border-0">
                    <th scope="row" className={theme.calendar.rowHeader} data-testid={`calendar-month-${row.short}`}>
                      {row.short}
                    </th>
                    {row.cells.map((cell, i) => (
                      <td key={keys[i]} className="px-1.5 py-1.5 align-top">
                        <MonthCell cell={cell} datasetKey={keys[i]} onClick={handleCellClick} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className={theme.calendar.legend} data-testid="calendar-legend">
          <span><span aria-hidden>✓</span> Uploaded</span>
          <span><span aria-hidden>✗</span> Missing</span>
          <span><span aria-hidden>⚠</span> Duplicate Upload</span>
          <span><span aria-hidden>⏳</span> Processing</span>
        </div>
      </div>

      {modal && (
        <MonthCellModal
          cell={modal.cell}
          datasetKey={modal.datasetKey}
          gstin={gstin}
          onClose={() => setModal(null)}
          onResolve={onResolveDuplicate}
        />
      )}
    </>
  );
}
