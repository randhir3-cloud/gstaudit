import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import DealerHeader from '../components/DealerHeader';
import ComparisonRecordsTable from '../components/investigation/ComparisonRecordsTable';
import { useDealer } from '../context/DealerContext';
import { useAuditSession } from '../context/AuditSessionContext';
import { fetchComparisonDetails } from '../api/comparison';

const FILTER_LABELS = {
  MISSING_IN_GSTR1: 'Missing in GSTR-1',
  MISSING_IN_EWAY: 'Missing in EWB',
  GSTIN_MISMATCH: 'GSTIN Mismatch',
  VALUE_MISMATCH: 'Value Mismatch',
  DATE_MISMATCH: 'Date Mismatch',
  DUPLICATE: 'Duplicates',
  MATCHED: 'Matched',
  ALL: 'All Records',
};

export default function WorkbookViewer() {
  const { workbookId, sourceFiles, currentDataset } = useDealer();
  const { session } = useAuditSession();
  const [searchParams] = useSearchParams();
  const filter = searchParams.get('filter') || 'ALL';
  const [details, setDetails] = useState({ records: [], total: 0 });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!session.session_id || filter === 'ALL') return;
    setLoading(true);
    fetchComparisonDetails(session.session_id, filter, { limit: 500 })
      .then(setDetails)
      .finally(() => setLoading(false));
  }, [session.session_id, filter]);

  const showComparisonTable = filter !== 'ALL' && session.session_id;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-zinc-950 dark:text-white">Workbook Viewer</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">Comparison detail view and workbook metadata.</p>
      </div>

      <DealerHeader />

      {showComparisonTable ? (
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5" data-testid="comparison-detail-table">
          <h3 className="font-semibold mb-1">{FILTER_LABELS[filter] || filter}</h3>
          <p className="text-xs text-zinc-500 mb-4">{details.total} records {loading ? '(loading…)' : ''}</p>
          <ComparisonRecordsTable records={details.records || []} testIdPrefix="workbook" />
        </div>
      ) : (
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 space-y-3">
          <h3 className="font-semibold">Workbook Details</h3>
          <p className="text-sm"><span className="text-zinc-500">Workbook ID:</span> {workbookId || '—'}</p>
          <p className="text-sm"><span className="text-zinc-500">Current Dataset:</span> {currentDataset || '—'}</p>
          {sourceFiles.length > 0 ? (
            <ul className="text-sm space-y-1 list-disc list-inside text-zinc-700 dark:text-zinc-300">
              {sourceFiles.map((file) => <li key={file}>{file}</li>)}
            </ul>
          ) : (
            <p className="text-sm text-zinc-500">Run comparison and open Investigation for case management.</p>
          )}
        </div>
      )}
    </div>
  );
}
