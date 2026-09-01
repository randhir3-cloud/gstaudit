/** Column definitions for comparison DataTable — import in pages, never inline. */

export const comparisonDetailColumns = [
  {
    key: 'invoice_number',
    label: 'Invoice',
    render: (row) => row.invoice_number || row.normalized_invoice,
    className: 'font-mono',
  },
  { key: 'result_type', label: 'Type', render: (row) => row.result_type || row.comparison_result },
  { key: 'risk_score', label: 'Risk' },
  { key: 'taxable_value_gstr1', label: 'GSTR-1 Value', sortable: false },
  { key: 'taxable_value_ewb', label: 'EWB Value', sortable: false },
  { key: 'source_period', label: 'Period', sortable: false },
];

export const comparisonSearchKeys = [
  'invoice_number',
  'normalized_invoice',
  'supplier_gstin',
  'gstin_gstr1',
];

export default comparisonDetailColumns;
