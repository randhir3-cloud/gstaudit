import React from 'react';
import { formatCount, formatPercent } from '../../utils/formatNumbers';
import SummaryCard from '../cards/SummaryCard';

export default function TopSummaryPanel({ summary }) {
  if (!summary) return null;

  const items = [
    { label: 'Files Uploaded', value: formatCount(summary.files_uploaded), testId: 'top-files' },
    { label: 'Rows Imported', value: formatCount(summary.rows_imported ?? summary.total_rows), testId: 'top-rows' },
    { label: 'Unique Records', value: formatCount(summary.unique_records), testId: 'top-unique' },
    { label: 'Duplicate Records', value: formatCount(summary.duplicate_records), testId: 'top-duplicates' },
    { label: 'Duplicate %', value: formatPercent(summary.duplicate_percent), testId: 'top-dup-pct' },
  ];

  return (
    <SummaryCard title="Upload Summary" items={items} testId="top-summary-panel" />
  );
}
