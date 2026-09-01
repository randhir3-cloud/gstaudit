import React, { useMemo } from 'react';
import DataTable from '../common/DataTable';
import ContentCard from '../cards/ContentCard';
import EmptyState from '../common/EmptyState';
import { uploadHistoryColumns, uploadSearchKeys } from '../../columns/uploadColumns';

export default function UploadHistoryTable({ history }) {
  const rows = useMemo(() => [...(history || [])].reverse().slice(0, 100), [history]);

  if (!rows.length) {
    return (
      <ContentCard title="Upload History" testId="upload-history">
        <EmptyState title="No uploads recorded yet." />
      </ContentCard>
    );
  }

  return (
    <ContentCard title="Upload History" testId="upload-history" noPadding>
      <DataTable
        data={rows}
        columns={uploadHistoryColumns}
        searchKeys={uploadSearchKeys}
        searchPlaceholder="Search uploads…"
        defaultSortKey="timestamp"
        defaultSortDir="desc"
        testIdPrefix="upload-history"
        pageSize={20}
      />
    </ContentCard>
  );
}
