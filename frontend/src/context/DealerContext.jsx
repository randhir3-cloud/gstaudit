import React, { createContext, useContext, useMemo, useState } from 'react';
import { EMPTY_DEALER } from '../types/dealer';

const DealerContext = createContext(null);

export function DealerProvider({ children }) {
  const [workbookId, setWorkbookId] = useState('');
  const [dealer, setDealer] = useState(EMPTY_DEALER);
  const [returnType, setReturnType] = useState('');
  const [sourceFiles, setSourceFiles] = useState([]);
  const [currentDataset, setCurrentDataset] = useState('');

  const setWorkbookMetadata = (metadata) => {
    if (!metadata) return;
    setWorkbookId(metadata.workbook_id || '');
    setDealer(metadata.dealer || EMPTY_DEALER);
    setReturnType(metadata.return_type || '');
    setSourceFiles(metadata.source_files || []);
    setCurrentDataset(metadata.current_dataset || '');
  };

  const clearDealer = () => {
    setWorkbookId('');
    setDealer(EMPTY_DEALER);
    setReturnType('');
    setSourceFiles([]);
    setCurrentDataset('');
  };

  const value = useMemo(
    () => ({
      workbookId,
      dealer,
      returnType,
      sourceFiles,
      currentDataset,
      setWorkbookMetadata,
      setCurrentDataset,
      clearDealer,
      hasDealer: Boolean(dealer?.gstin),
    }),
    [workbookId, dealer, returnType, sourceFiles, currentDataset],
  );

  return <DealerContext.Provider value={value}>{children}</DealerContext.Provider>;
}

export function useDealer() {
  const context = useContext(DealerContext);
  if (!context) {
    throw new Error('useDealer must be used within DealerProvider');
  }
  return context;
}
