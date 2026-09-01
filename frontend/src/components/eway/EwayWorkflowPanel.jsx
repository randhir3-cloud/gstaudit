import React, { useState, useRef } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Download,
  Eye,
  HelpCircle,
  Loader2,
} from 'lucide-react';
import { useEwayWorkflow } from '../../context/EwayContext';
import { useDealer } from '../../context/DealerContext';
import { useAuditSession } from '../../context/AuditSessionContext';
import { EMPTY_DEALER } from '../../types/dealer';
import { classifyEwayFiles, mergeEwayWorkflow } from '../../api/eway';
import {
  extractPeriodFromFilename,
  getFYMonthSortKey,
  downloadBlob,
} from '../../utils/fileHelpers';
import FileUploadZone from '../merge/FileUploadZone';
import UnifiedMergeFileList from '../merge/UnifiedMergeFileList';
import EwaySummaryCard from './EwaySummaryCard';
import WorkbookPreviewModal from './WorkbookPreviewModal';
import WrongUploadDialog from './WrongUploadDialog';
import DealerGstinModal from './DealerGstinModal';

export default function EwayWorkflowPanel({ direction, directionLabel }) {
  const {
    workflow,
    updateWorkflow,
    applyMergeResult,
    direction: workflowDirection,
    dealerGstin,
    dealerGstinSource,
    setResolvedDealerGstin,
    dealerGstinModalOpen,
    setDealerGstinModalOpen,
    moveFileToDirection,
    moveFilesToFreshDirection,
    pendingUploadQueue,
    setPendingUploadQueue,
  } = useEwayWorkflow(direction);

  const { dealer: gstrDealer } = useDealer();
  const { recordUpload, recordMerge } = useAuditSession();
  const [isDragOver, setIsDragOver] = useState(false);
  const pendingFilesRef = useRef(null);

  const effectiveDealerGstin = dealerGstin || gstrDealer?.gstin || '';

  const processClassificationResults = async (selectedFiles, classifyResponse) => {
    if (classifyResponse.dealer_resolution?.gstin && !dealerGstin) {
      setResolvedDealerGstin(
        classifyResponse.dealer_resolution.gstin,
        classifyResponse.dealer_resolution.source,
      );
    }

    if (classifyResponse.dealer_resolution?.requires_user_input && !effectiveDealerGstin) {
      pendingFilesRef.current = { files: selectedFiles, direction: workflowDirection };
      setPendingUploadQueue(pendingFilesRef.current);
      setDealerGstinModalOpen(true);
      return;
    }

    const wrongFiles = [];
    const validFilesToAdd = [];

    for (let i = 0; i < selectedFiles.length; i += 1) {
      const file = selectedFiles[i];
      const classification = classifyResponse.classifications[i];
      const fileEntry = {
        id: `file_${Date.now()}_${i}_${Math.random().toString(36).substr(2, 5)}`,
        file,
        name: file.name,
        size: file.size,
        period: extractPeriodFromFilename(file.name),
        classification,
      };

      if (classification.status === 'wrong_section') {
        wrongFiles.push(fileEntry);
      } else if (classification.status === 'unknown') {
        updateWorkflow({
          error: `${file.name}: ${classification.message}`,
        });
        return;
      } else {
        validFilesToAdd.push(fileEntry);
      }
    }

    // If any wrong-section files detected in this batch
    if (wrongFiles.length > 0) {
      const targetDir = wrongFiles[0].classification.detected_type;
      updateWorkflow({
        wrongUploadModal: {
          isOpen: true,
          fileEntry: wrongFiles[0],
          fileEntries: wrongFiles,
          detectedType: targetDir,
          targetDirection: targetDir,
        },
      });
      return;
    }

    // Otherwise add valid files to current section
    if (validFilesToAdd.length > 0) {
      updateWorkflow((prev) => {
        const combined = [...prev.files, ...validFilesToAdd].sort(
          (a, b) => getFYMonthSortKey(a.name) - getFYMonthSortKey(b.name),
        );
        const resolvedGstin = classifyResponse.dealer_resolution?.gstin || effectiveDealerGstin || validFilesToAdd[0]?.classification?.dealer_gstin || '';
        const resolvedLegalName = classifyResponse.dealer_resolution?.legal_name || prev.dealerMetadata?.legal_name || '';
        const resolvedFy = classifyResponse.dealer_resolution?.financial_year || validFilesToAdd[0]?.classification?.financial_year || prev.dealerMetadata?.financial_year || '';

        recordUpload(
          workflowDirection === 'outward' ? 'ewb_outward' : 'ewb_inward',
          validFilesToAdd.map((f) => f.name),
          {
            gstin: resolvedGstin,
            legal_name: resolvedLegalName,
            financial_year: resolvedFy,
          },
        );

        return {
          ...prev,
          files: combined,
          dealerMetadata: {
            ...prev.dealerMetadata,
            gstin: resolvedGstin,
            legal_name: resolvedLegalName,
            trade_name: resolvedLegalName,
            financial_year: resolvedFy,
          },
          summary: {
            ...(prev.summary || {}),
            financial_year: resolvedFy,
            row_count: (prev.summary?.row_count && prev.mergeStatus === 'merged') ? prev.summary.row_count : classifyResponse.dealer_resolution?.total_rows,
          },
          error: null,
          successMessage: null,
          mergeStatus: prev.mergeStatus === 'merged' ? 'idle' : prev.mergeStatus,
        };
      });
    }
  };

  const classifyAndAddFiles = async (selectedFiles) => {
    const validFiles = selectedFiles.filter((file) => {
      const name = file.name.toLowerCase();
      return name.endsWith('.xlsx') || name.endsWith('.xls');
    });

    if (validFiles.length === 0) {
      updateWorkflow({ error: 'Please select valid Excel files (.xlsx or .xls).' });
      return;
    }

    updateWorkflow({ isClassifying: true, error: null });
    try {
      const response = await classifyEwayFiles(validFiles, {
        dealerGstin: effectiveDealerGstin,
        expectedDirection: workflowDirection,
      });
      await processClassificationResults(validFiles, response);
    } catch (err) {
      updateWorkflow({ error: err.message });
    } finally {
      updateWorkflow({ isClassifying: false });
    }
  };

  const handleDealerGstinSubmit = async (gstin) => {
    const queued = pendingFilesRef.current || pendingUploadQueue;
    pendingFilesRef.current = null;
    setResolvedDealerGstin(gstin, 'user');
    setPendingUploadQueue(null);

    if (!queued?.files?.length || queued.direction !== workflowDirection) {
      return;
    }

    updateWorkflow({ isClassifying: true, error: null });
    try {
      const response = await classifyEwayFiles(queued.files, {
        dealerGstin: gstin,
        expectedDirection: workflowDirection,
      });
      await processClassificationResults(queued.files, response);
    } catch (err) {
      updateWorkflow({ error: err.message });
    } finally {
      updateWorkflow({ isClassifying: false });
    }
  };

  const removeFile = (id) => {
    updateWorkflow((prev) => {
      const remaining = prev.files.filter((f) => f.id !== id);
      if (remaining.length === 0) {
        return {
          ...prev,
          files: [],
          mergeStatus: 'idle',
          mergedWorkbook: null,
          summary: null,
          dealerMetadata: { ...EMPTY_DEALER },
          error: null,
          successMessage: null,
        };
      }
      return { ...prev, files: remaining };
    });
  };

  const clearAllFiles = () => {
    updateWorkflow({
      files: [],
      mergeStatus: 'idle',
      mergedWorkbook: null,
      summary: null,
      dealerMetadata: { ...EMPTY_DEALER },
      error: null,
      successMessage: null,
    });
  };

  const moveFile = (index, offset) => {
    updateWorkflow((prev) => {
      const copy = [...prev.files];
      const target = index + offset;
      if (target < 0 || target >= copy.length) return prev;
      [copy[index], copy[target]] = [copy[target], copy[index]];
      return { ...prev, files: copy };
    });
  };

  const triggerMerge = async (ignoreMissing = false) => {
    if (workflow.files.length === 0) {
      updateWorkflow({ error: 'Please add some Excel files first.' });
      return;
    }

    const hasBlocking = workflow.files.some(
      (f) => f.classification?.status && f.classification.status !== 'valid',
    );
    if (hasBlocking) {
      updateWorkflow({ error: 'Resolve all validation issues before merging.' });
      return;
    }

    updateWorkflow({ mergeStatus: 'merging', error: null, successMessage: null });

    try {
      const result = await mergeEwayWorkflow(
        workflow.files.map((f) => f.file),
        workflowDirection,
        ignoreMissing,
        effectiveDealerGstin,
      );
      applyMergeResult(result);
      recordMerge(workflowDirection === 'outward' ? 'ewb_outward' : 'ewb_inward', result);
    } catch (err) {
      if (err.payload?.error_type === 'missing_months') {
        updateWorkflow({
          mergeStatus: 'idle',
          warningModal: { isOpen: true, missingMonths: err.payload.missing || [] },
        });
        return;
      }
      updateWorkflow({ mergeStatus: 'error', error: err.message });
    }
  };

  const handleDownload = () => {
    if (!workflow.mergedWorkbook) return;
    downloadBlob(workflow.mergedWorkbook.blob, workflow.mergedWorkbook.filename);
  };

  const wrongModal = workflow.wrongUploadModal || {};

  return (
    <div className="space-y-6">
      <EwaySummaryCard workflow={workflow} directionLabel={directionLabel} />

      {workflow.error && (
        <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 text-rose-800 dark:text-rose-300 rounded-xl p-4 flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div className="text-sm"><span className="font-semibold">Error:</span> {workflow.error}</div>
        </div>
      )}

      {workflow.successMessage && (
        <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-400 rounded-xl p-4 flex items-start space-x-3">
          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div className="text-sm"><span className="font-semibold">Success!</span> {workflow.successMessage}</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={`lg:col-span-1 space-y-6 ${workflow.files.length === 0 ? 'lg:col-span-3 max-w-2xl mx-auto w-full' : ''}`}>
          <div className="relative">
            <FileUploadZone
              isDragOver={isDragOver}
              onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragOver(false);
                if (e.dataTransfer.files) classifyAndAddFiles(Array.from(e.dataTransfer.files));
              }}
              onFilesSelected={classifyAndAddFiles}
            />
            {workflow.isClassifying && (
              <div className="absolute inset-0 bg-white/70 dark:bg-zinc-950/70 rounded-2xl flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
              </div>
            )}
          </div>

          {workflow.files.length > 0 && (
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-4 shadow-sm">
              <h3 className="font-bold text-zinc-950 dark:text-zinc-100 text-sm tracking-wide uppercase">Merge Settings</h3>
              <button
                type="button"
                onClick={() => triggerMerge(false)}
                disabled={workflow.mergeStatus === 'merging' || workflow.isClassifying}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 dark:bg-zinc-800 text-white font-medium py-3 rounded-xl flex items-center justify-center gap-2"
              >
                {workflow.mergeStatus === 'merging' ? <><Loader2 className="h-5 w-5 animate-spin" />Merging…</> : <><Download className="h-5 w-5" />Merge Workbook</>}
              </button>
              {workflow.mergeStatus === 'merged' && (
                <div className="grid grid-cols-2 gap-2">
                  <button type="button" onClick={() => updateWorkflow({ previewOpen: true })} className="inline-flex items-center justify-center gap-2 bg-zinc-100 dark:bg-zinc-800 py-2.5 rounded-xl text-sm font-medium"><Eye className="h-4 w-4" />Preview</button>
                  <button type="button" onClick={handleDownload} className="inline-flex items-center justify-center gap-2 bg-emerald-600 text-white py-2.5 rounded-xl text-sm font-medium"><Download className="h-4 w-4" />Download</button>
                </div>
              )}
            </div>
          )}
        </div>

        {workflow.files.length > 0 && (
          <div className="lg:col-span-2">
            <UnifiedMergeFileList
              files={workflow.files}
              mode="eway"
              onMoveUp={(index) => moveFile(index, -1)}
              onMoveDown={(index) => moveFile(index, 1)}
              onRemove={removeFile}
              onClearAll={clearAllFiles}
              notice={(
                <div>
                  <span className="font-semibold text-zinc-700 dark:text-zinc-200">Intelligent classification:</span> Files are inspected by content. Wrong-section uploads are detected automatically.
                </div>
              )}
            />
          </div>
        )}
      </div>

      <WorkbookPreviewModal
        isOpen={workflow.previewOpen}
        onClose={() => updateWorkflow({ previewOpen: false })}
        preview={workflow.summary?.preview}
        filename={workflow.mergedWorkbook?.filename || workflow.outputName}
      />

      <DealerGstinModal
        isOpen={dealerGstinModalOpen}
        onSubmit={handleDealerGstinSubmit}
        onCancel={() => { setDealerGstinModalOpen(false); setPendingUploadQueue(null); }}
      />

      <WrongUploadDialog
        isOpen={wrongModal.isOpen}
        detectedType={wrongModal.detectedType}
        targetDirection={wrongModal.targetDirection}
        filename={
          wrongModal.fileEntries?.length > 1
            ? `${wrongModal.fileEntries.length} files (${wrongModal.fileEntries.map((f) => f.name).slice(0, 2).join(', ')}${wrongModal.fileEntries.length > 2 ? '...' : ''})`
            : wrongModal.fileEntry?.name
        }
        onMove={() => {
          const filesToMove = wrongModal.fileEntries?.length ? wrongModal.fileEntries : (wrongModal.fileEntry ? [wrongModal.fileEntry] : []);
          if (filesToMove.length > 0 && wrongModal.targetDirection) {
            moveFilesToFreshDirection(filesToMove, wrongModal.targetDirection, workflowDirection);
          }
        }}
        onCancel={() => updateWorkflow({
          wrongUploadModal: { isOpen: false, fileEntry: null, fileEntries: [], detectedType: '', targetDirection: '' },
        })}
      />

      {workflow.warningModal?.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-zinc-900 rounded-2xl border shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center gap-3 text-amber-600 mb-4">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="text-lg font-bold">Missing Months Detected</h3>
            </div>
            <ul className="text-sm space-y-1 mb-6">
              {workflow.warningModal.missingMonths.map((month) => <li key={month}>{month}</li>)}
            </ul>
            <div className="flex gap-3">
              <button type="button" onClick={() => updateWorkflow({ warningModal: { isOpen: false, missingMonths: [] } })} className="flex-1 py-2.5 rounded-xl bg-zinc-100 dark:bg-zinc-800 text-sm">Cancel</button>
              <button type="button" onClick={() => triggerMerge(true)} className="flex-1 py-2.5 rounded-xl bg-amber-600 text-white text-sm">Merge anyway</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
