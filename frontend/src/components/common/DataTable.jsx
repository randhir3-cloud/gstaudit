import React, { useMemo, useState } from 'react';
import { cn } from '../../lib/utils';
import { tableShell, tableBase, tableHead, tableRow, tableRowSelected, tableCell, tableHeaderCell } from '../../theme/tables';
import SearchBar from './SearchBar';
import EmptyState from './EmptyState';
import { useSorting } from '../../hooks/useSorting';
import { useSearch } from '../../hooks/useSearch';
import { usePagination } from '../../hooks/usePagination';

const DEFAULT_PAGE_SIZE = 25;

/**
 * Unified DataTable — sorting, search, pagination, selection, sticky header.
 * @param {Object} props
 * @param {Array} props.data
 * @param {Array<{key:string,label:string,sortable?:boolean,render?:(row)=>ReactNode,className?:string}>} props.columns
 */
export default function DataTable({
  data = [],
  columns = [],
  pageSize = DEFAULT_PAGE_SIZE,
  defaultSortKey,
  defaultSortDir = 'desc',
  searchKeys = [],
  searchPlaceholder = 'Search…',
  selectable = false,
  selectedIds = [],
  getRowId = (row, index) => row.id ?? row.case_id ?? String(index),
  getRowTestId,
  onSelect,
  onSelectAll,
  onRowClick,
  emptyMessage = 'No records.',
  testIdPrefix = 'data-table',
  maxHeight = '480px',
  className,
}) {
  const { search, setSearch, filterRows } = useSearch();
  const { sortKey, sortDir, toggleSort, sortRows } = useSorting(defaultSortKey || columns[0]?.key, defaultSortDir);

  const filtered = useMemo(() => {
    let rows = filterRows(data, searchKeys.length ? searchKeys : columns.map((c) => c.key));
    return sortRows(rows, sortKey, (row) => row[sortKey] ?? '');
  }, [data, search, searchKeys, columns, sortKey, sortDir, filterRows, sortRows]);

  const { page, setPage, pageCount, pageRows } = usePagination(filtered, pageSize);

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(0);
  };

  return (
    <div className={className} data-testid={`${testIdPrefix}-records-table`}>
      <SearchBar
        value={search}
        onChange={handleSearchChange}
        placeholder={searchPlaceholder}
        testId={`${testIdPrefix}-search`}
        recordCount={filtered.length}
        className="mb-3"
      />
      <div className={cn(tableShell)} style={{ maxHeight }}>
        <table className={tableBase}>
          <thead className={tableHead}>
            <tr>
              {selectable && (
                <th className={tableHeaderCell}>
                  <input
                    type="checkbox"
                    aria-label="Select all"
                    onChange={(e) => onSelectAll?.(e.target.checked, pageRows)}
                  />
                </th>
              )}
              {columns.map((col) => (
                <th key={col.key} className={cn(tableHeaderCell, col.className)}>
                  {col.sortable !== false ? (
                    <button
                      type="button"
                      className="font-semibold hover:text-primary"
                      onClick={() => toggleSort(col.key)}
                    >
                      {col.label}
                      {sortKey === col.key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
                    </button>
                  ) : (
                    col.label
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => {
              const rowId = getRowId(row, page * pageSize + i);
              const rowKey = `${rowId}-${page * pageSize + i}`;
              const selected = selectedIds.includes(row.case_id ?? rowId);
              return (
                <tr
                  key={rowKey}
                  className={cn(
                    tableRow,
                    'cursor-pointer',
                    selected && tableRowSelected,
                  )}
                  onClick={() => onRowClick?.(row)}
                  data-testid={
                    getRowTestId
                      ? getRowTestId(row, page * pageSize + i)
                      : `${testIdPrefix}-row-${i}`
                  }
                >
                  {selectable && (
                    <td className={tableCell} onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selected}
                        aria-label={`Select row ${rowId}`}
                        onChange={() => onSelect?.(row.case_id ?? rowId)}
                      />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td key={col.key} className={cn(tableCell, col.className)}>
                      {col.render ? col.render(row) : (row[col.key] ?? '—')}
                    </td>
                  ))}
                </tr>
              );
            })}
            {!pageRows.length && (
              <tr>
                <td colSpan={columns.length + (selectable ? 1 : 0)} className="px-3 py-8">
                  <EmptyState title={emptyMessage} />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between mt-2 text-xs">
        <button
          type="button"
          disabled={page <= 0}
          onClick={() => setPage((p) => p - 1)}
          className="px-2 py-1 rounded bg-secondary disabled:opacity-40"
        >
          Prev
        </button>
        <span className="tabular-nums">Page {page + 1} / {pageCount}</span>
        <button
          type="button"
          disabled={page >= pageCount - 1}
          onClick={() => setPage((p) => p + 1)}
          className="px-2 py-1 rounded bg-secondary disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
