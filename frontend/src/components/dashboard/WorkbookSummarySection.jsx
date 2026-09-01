import React from 'react';
import DataTable from '../common/DataTable';
import ContentCard from '../cards/ContentCard';
import { workbookColumns, workbookSearchKeys } from '../../columns/workbookColumns';

export default function WorkbookSummarySection({ summaries }) {
  if (!summaries?.length) return null;

  const data = summaries.map((w) => ({
    ...w,
    id: w.dataset_key,
  }));

  return (
    <ContentCard title="Workbook Summary" testId="workbook-summary" noPadding>
      <DataTable
        data={data}
        columns={workbookColumns}
        searchKeys={workbookSearchKeys}
        searchPlaceholder="Search workbooks…"
        defaultSortKey="dataset_label"
        testIdPrefix="workbook-summary"
        pageSize={10}
        getRowId={(row) => row.dataset_key}
      />
    </ContentCard>
  );
}
