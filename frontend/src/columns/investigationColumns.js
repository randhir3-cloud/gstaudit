/** Column definitions for investigation workbench DataTable. */

export const investigationColumns = [
  {
    key: 'invoice_number',
    label: 'Invoice',
    render: (row) => row.invoice_number || row.normalized_invoice,
    className: 'font-mono',
  },
  { key: 'result_type', label: 'Type', render: (row) => row.result_type || row.comparison_result },
  { key: 'risk_score', label: 'Risk' },
  { key: 'status', label: 'Status', sortable: false },
  { key: 'source_period', label: 'Period', sortable: false },
];

export const investigationSearchKeys = [
  'invoice_number',
  'normalized_invoice',
  'case_number',
  'supplier_gstin',
  'gstin_gstr1',
];

export default investigationColumns;
