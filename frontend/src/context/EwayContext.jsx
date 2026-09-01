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
  const [activeSubTab, setActiveSubTab] = useState('outward');
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

  const applyMergeResult = useCallback((direction, result) => {
    const blob = result.blob
      ? result.blob
      : base64ToBlob(
          result.workbook_base64,
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        );
    const { workbook_base64, blob: _b, ...summary } = result;

    updateWorkflow(direction, {
      mergeStatus: 'merged',
      mergedWorkbook: { blob, filename: result.suggested_filename },
      summary,
      dealerMetadata: result.dealer || { ...EMPTY_DEALER },
      outputName: result.suggested_filename,
      error: null,
      successMessage: `Merged ${result.row_count} rows across ${result.sheet_list.length} sheet(s).`,
      warningModal: { isOpen: false, missingMonths: [] },
    });
  }, [updateWorkflow]);

  const setResolvedDealerGstin = useCallback((gstin, source = 'user') => {
    setDealerGstin(gstin);
    setDealerGstinSource(source);
    setDealerGstinModalOpen(false);
  }, []);

  const moveFileToDirection = useCallback((fileEntry, targetDirection, sourceDirection) => {
    updateWorkflow(sourceDirection, (prev) => ({
      ...prev,
      files: prev.files.filter((f) => f.id !== fileEntry.id),
      wrongUploadModal: { isOpen: false, fileEntry: null, detectedType: '', targetDirection: '' },
    }));
    updateWorkflow(targetDirection, (prev) => ({
      ...prev,
      files: [...prev.files, { ...fileEntry, classification: { ...fileEntry.classification, status: 'valid' } }],
      successMessage: `Moved ${fileEntry.name} to ${targetDirection.toUpperCase()} section.`,
    }));
    if (targetDirection !== activeSubTab) {
      setActiveSubTab(targetDirection);
    }
  }, [updateWorkflow, activeSubTab]);

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
      applyMergeResult,
      moveFileToDirection,
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
      applyMergeResult,
      moveFileToDirection,
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
