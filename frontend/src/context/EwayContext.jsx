import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { EMPTY_DEALER } from '../types/dealer';
import { base64ToBlob } from '../utils/fileHelpers';

const EwayContext = createContext(null);

function createInitialWorkflow(direction) {
  return {
    direction,
    files: [],
    mergeStatus: 'idle',
    error: null,
    successMessage: null,
    warningModal: { isOpen: false, missingMonths: [] },
    wrongUploadModal: { isOpen: false, fileEntry: null, detectedType: '', targetDirection: '' },
    unknownModal: { isOpen: false, fileEntry: null, classification: null },
    mergedWorkbook: null,
    summary: null,
    dealerMetadata: { ...EMPTY_DEALER },
    previewOpen: false,
    outputName: direction === 'outward' ? 'EWB_Outward_Merged.xlsx' : 'EWB_Inward_Merged.xlsx',
    isClassifying: false,
  };
}

export function EwayProvider({ children }) {
  const [outward, setOutward] = useState(() => createInitialWorkflow('outward'));
  const [inward, setInward] = useState(() => createInitialWorkflow('inward'));
  const [activeSubTab, setActiveSubTab] = useState('inward');
  const [dealerGstin, setDealerGstin] = useState('');
  const [dealerGstinSource, setDealerGstinSource] = useState('none');
  const [dealerGstinModalOpen, setDealerGstinModalOpen] = useState(false);
  const [pendingUploadQueue, setPendingUploadQueue] = useState(null);

  const getWorkflow = useCallback(
    (direction) => (direction === 'inward' ? inward : outward),
    [inward, outward],
  );

  const updateWorkflow = useCallback((direction, updater) => {
    if (direction === 'inward') {
      setInward((prev) => (typeof updater === 'function' ? updater(prev) : { ...prev, ...updater }));
    } else {
      setOutward((prev) => (typeof updater === 'function' ? updater(prev) : { ...prev, ...updater }));
    }
  }, []);

  const resetDirection = useCallback((direction) => {
    if (direction === 'inward') {
      setInward(createInitialWorkflow('inward'));
    } else {
      setOutward(createInitialWorkflow('outward'));
    }
  }, []);

  const applyMergeResult = useCallback((direction, result) => {
    const blob = result.blob
      ? result.blob
      : base64ToBlob(
          result.workbook_base64,
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        );
    const { workbook_base64, blob: _b, ...summary } = result;

    const parts = [`${result.source_files?.length || 0} files merged`];
    if (result.previously_merged_excluded) {
      parts.push(`${result.previously_merged_excluded} merged output excluded`);
    }
    if (result.duplicate_files_skipped) {
      parts.push(`${result.duplicate_files_skipped} duplicate files skipped`);
    }
    if (result.duplicate_rows_skipped > 0) {
      parts.push(`${result.duplicate_rows_skipped} duplicate records removed`);
    }
    parts.push(`${result.row_count || 0} final records`);

    updateWorkflow(direction, {
      mergeStatus: 'merged',
      mergedWorkbook: { blob, filename: result.suggested_filename },
      summary,
      dealerMetadata: result.dealer || { ...EMPTY_DEALER },
      outputName: result.suggested_filename,
      error: null,
      successMessage: `Merged successfully · ${parts.join(' · ')}`,
      warningModal: { isOpen: false, missingMonths: [] },
    });
  }, [updateWorkflow]);

  const setResolvedDealerGstin = useCallback((gstin, source = 'user') => {
    setDealerGstin(gstin);
    setDealerGstinSource(source);
    setDealerGstinModalOpen(false);
  }, []);

  /** Atomically resets the target direction, removes files from source if present, and sets moved files on fresh target */
  const moveFilesToFreshDirection = useCallback((filesToMove, targetDirection, sourceDirection) => {
    const fileEntries = Array.isArray(filesToMove) ? filesToMove : [filesToMove];
    const fileIdsToRemove = new Set(fileEntries.map((f) => f.id));

    // 1. Clean source workflow
    if (sourceDirection) {
      updateWorkflow(sourceDirection, (prev) => ({
        ...prev,
        files: prev.files.filter((f) => !fileIdsToRemove.has(f.id)),
        wrongUploadModal: { isOpen: false, fileEntries: [], detectedType: '', targetDirection: '' },
      }));
    }

    // 2. Completely fresh target workflow with ONLY the moved file(s)
    const freshTarget = createInitialWorkflow(targetDirection);
    freshTarget.files = fileEntries.map((f) => ({
      ...f,
      classification: {
        ...f.classification,
        status: 'valid',
        detected_type: targetDirection,
      },
    }));
    const filenames = fileEntries.map((f) => f.name).join(', ');
    freshTarget.successMessage = `Moved ${filenames} to ${targetDirection.toUpperCase()} section.`;

    if (targetDirection === 'inward') {
      setInward(freshTarget);
    } else {
      setOutward(freshTarget);
    }

    // 3. Switch active tab to target
    setActiveSubTab(targetDirection);
  }, [updateWorkflow]);

  const moveFileToDirection = useCallback((fileEntry, targetDirection, sourceDirection) => {
    moveFilesToFreshDirection([fileEntry], targetDirection, sourceDirection);
  }, [moveFilesToFreshDirection]);

  const value = useMemo(
    () => ({
      outward,
      inward,
      activeSubTab,
      setActiveSubTab,
      dealerGstin,
      dealerGstinSource,
      dealerGstinModalOpen,
      setDealerGstinModalOpen,
      setResolvedDealerGstin,
      pendingUploadQueue,
      setPendingUploadQueue,
      getWorkflow,
      updateWorkflow,
      resetDirection,
      applyMergeResult,
      moveFileToDirection,
      moveFilesToFreshDirection,
    }),
    [
      outward,
      inward,
      activeSubTab,
      dealerGstin,
      dealerGstinSource,
      dealerGstinModalOpen,
      setResolvedDealerGstin,
      pendingUploadQueue,
      getWorkflow,
      updateWorkflow,
      resetDirection,
      applyMergeResult,
      moveFileToDirection,
      moveFilesToFreshDirection,
    ],
  );

  return <EwayContext.Provider value={value}>{children}</EwayContext.Provider>;
}

export function useEway() {
  const context = useContext(EwayContext);
  if (!context) throw new Error('useEway must be used within EwayProvider');
  return context;
}

export function useEwayWorkflow(direction) {
  const ctx = useEway();
  return {
    ...ctx,
    workflow: ctx.getWorkflow(direction),
    updateWorkflow: (updater) => ctx.updateWorkflow(direction, updater),
    applyMergeResult: (result) => ctx.applyMergeResult(direction, result),
    direction,
  };
}
