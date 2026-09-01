import React from 'react';
import DataTable from '../../../components/common/DataTable';
import { investigationColumns, investigationSearchKeys } from '../../../columns/investigationColumns';

export default function CaseTable({
  records = [],
  selectedIds = [],
  onSelect,
  onSelectAll,
  onRowClick,
  selectable = false,
  testIdPrefix = 'investigation',
}) {
  return (
    <DataTable
      data={records}
      columns={investigationColumns}
      defaultSortKey="risk_score"
      defaultSortDir="desc"
      searchKeys={investigationSearchKeys}
      searchPlaceholder="Search invoice, GSTIN, case…"
      selectable={selectable}
      selectedIds={selectedIds}
      onSelect={onSelect}
      onSelectAll={onSelectAll}
      onRowClick={onRowClick}
      testIdPrefix={testIdPrefix}
      getRowId={(row, index) => row.case_id || row.normalized_invoice || String(index)}
    />
  );
}
