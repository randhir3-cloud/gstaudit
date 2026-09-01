import { formatCount } from '../utils/formatNumbers';

export const workbookColumns = [
  { key: 'dataset_label', label: 'Workbook', render: (row) => row.dataset_label, className: 'font-medium' },
  { key: 'sheets', label: 'Sheets', sortable: false },
  { key: 'rows', label: 'Rows', render: (row) => formatCount(row.rows) },
  { key: 'columns', label: 'Columns', sortable: false },
  { key: 'files', label: 'Files' },
  { key: 'months', label: 'Months' },
  { key: 'duplicate_records', label: 'Duplicates', render: (row) => formatCount(row.duplicate_records) },
  { key: 'unique_records', label: 'Unique', render: (row) => formatCount(row.unique_records) },
];

export const workbookSearchKeys = ['dataset_label', 'dataset_key'];

export default workbookColumns;
