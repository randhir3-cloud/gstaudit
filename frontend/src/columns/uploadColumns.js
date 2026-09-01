import { formatDate } from '../utils/formatNumbers';

export const uploadHistoryColumns = [
  {
    key: 'timestamp',
    label: 'Time',
    sortable: false,
    render: (row) => (row.timestamp ? new Date(row.timestamp).toLocaleString() : '—'),
  },
  { key: 'dataset_label', label: 'Dataset' },
  { key: 'month', label: 'Month', sortable: false },
  {
    key: 'filename',
    label: 'Filename',
    className: 'font-mono text-xs max-w-[200px] truncate',
    render: (row) => row.filename,
  },
  { key: 'rows', label: 'Rows', sortable: false },
  { key: 'status', label: 'Status', sortable: false },
];

export const uploadSearchKeys = ['filename', 'dataset_label', 'month', 'status'];

export default uploadHistoryColumns;
