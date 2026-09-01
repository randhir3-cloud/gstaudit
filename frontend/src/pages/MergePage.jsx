import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  FileSpreadsheet,
  Trash2,
  Loader2,
  ArrowUp,
  ArrowDown,
  Download,
  AlertTriangle,
  FileText,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import DealerHeader from '../components/DealerHeader';
import EwayBillSection from '../components/eway/EwayBillSection';
import { useDealer } from '../context/DealerContext';
import { useAuditSession } from '../context/AuditSessionContext';
import {
  extractDealerMetadata,
  formatDealerMismatchError,
  parseWorkbookMetadataHeader,
} from '../api/dealer';
import { authHeaders } from '../api/client';
import {
  extractPeriodFromFilename,
  formatBytes,
  getFYMonthSortKey,
} from '../utils/fileHelpers';

const API_BASE_URL = '';

export default function MergePage() {
  const { setWorkbookMetadata, clearDealer } = useDealer();
  const { recordUpload, recordMerge } = useAuditSession();
  const [activeTab, setActiveTab] = useState('gstr2a');
  const [files, setFiles] = useState([]);
  const [outputName, setOutputName] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [warningModal, setWarningModal] = useState({ isOpen: false, missingMonths: [] });

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (activeTab === 'gstr2a') {
      setOutputName('GSTR2A_Merged.xlsx');
    } else if (activeTab === 'gstr1') {
      setOutputName('GSTR1_Merged.xlsx');
    }
    if (activeTab === 'gstr1' || activeTab === 'gstr2a') {
      setFiles([]);
      setError(null);
      setSuccessMessage(null);
    }
  }, [activeTab]);

  const refreshDealerMetadata = async (fileEntries) => {
    if (activeTab !== 'gstr1' && activeTab !== 'gstr2a') return;
    if (fileEntries.length === 0) {
      clearDealer();
      return;
    }

    setIsExtracting(true);
    try {
      const metadata = await extractDealerMetadata(
        fileEntries.map((entry) => entry.file),
        activeTab,
      );
      setWorkbookMetadata(metadata);
      recordUpload(
        activeTab,
        fileEntries.map((e) => e.name),
        metadata.dealer,
      );
    } catch (err) {
      clearDealer();
      if (err.payload?.error_type === 'dealer_mismatch' || err.payload?.error_type === 'dealer_metadata_missing') {
        setError(formatDealerMismatchError(err.payload));
      } else {
        setError(err.message);
      }
    } finally {
      setIsExtracting(false);
    }
  };

  const handleFileChange = (e) => {
    addFilesToList(Array.from(e.target.files));
  };

  const addFilesToList = (selectedFiles) => {
    setError(null);
    setSuccessMessage(null);

    const validFiles = selectedFiles.filter((file) => {
      const name = file.name.toLowerCase();
      return name.endsWith('.xlsx') || name.endsWith('.xls');
    });

    if (validFiles.length === 0) {
      setError('Please select valid Excel files (.xlsx or .xls).');
      return;
    }

    const newFiles = validFiles.map((file, index) => ({
      id: `file_${Date.now()}_${index}_${Math.random().toString(36).substr(2, 5)}`,
      file,
      name: file.name,
      size: file.size,
      period: (activeTab === 'gstr1' || activeTab === 'gstr2a')
        ? extractPeriodFromFilename(file.name)
        : null,
    }));

    setFiles((prev) => {
      const combined = [...prev, ...newFiles];
      if (activeTab === 'gstr1' || activeTab === 'gstr2a') {
        combined.sort((a, b) => getFYMonthSortKey(a.name) - getFYMonthSortKey(b.name));
      }
      refreshDealerMetadata(combined);
      return combined;
    });

    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (id) => {
    setFiles((prev) => {
      const next = prev.filter((f) => f.id !== id);
      refreshDealerMetadata(next);
      return next;
    });
  };

  const clearAllFiles = () => {
    setFiles([]);
    clearDealer();
    setError(null);
    setSuccessMessage(null);
  };

  const moveFileUp = (index) => {
    if (index === 0) return;
    setFiles((prev) => {
      const copy = [...prev];
      [copy[index - 1], copy[index]] = [copy[index], copy[index - 1]];
      refreshDealerMetadata(copy);
      return copy;
    });
  };

  const moveFileDown = (index) => {
    setFiles((prev) => {
      if (index === prev.length - 1) return prev;
      const copy = [...prev];
      [copy[index + 1], copy[index]] = [copy[index], copy[index + 1]];
      refreshDealerMetadata(copy);
      return copy;
    });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => setIsDragOver(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) addFilesToList(Array.from(e.dataTransfer.files));
  };

  const triggerMerge = async (ignoreMissing = false) => {
    if (files.length === 0) {
      setError('Please add some Excel files first.');
      return;
    }

    setIsMerging(true);
    setError(null);
    setSuccessMessage(null);

    const formData = new FormData();
    files.forEach((f) => formData.append('files', f.file));

    const endpoint = activeTab === 'gstr2a'
      ? '/api/merge/gstr2a'
      : '/api/merge/gstr1';
    const queryParam = `?ignore_missing=${ignoreMissing}`;

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}${queryParam}`, {
        method: 'POST',
        headers: authHeaders(),
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();

        if ((activeTab === 'gstr1' || activeTab === 'gstr2a') && errorData.error_type === 'missing_months') {
          setWarningModal({ isOpen: true, missingMonths: errorData.missing });
          setIsMerging(false);
          return;
        }

        if (errorData.error_type === 'dealer_mismatch' || errorData.error_type === 'dealer_metadata_missing') {
          throw new Error(formatDealerMismatchError(errorData));
        }

        throw new Error(errorData.detail || errorData.message || 'An error occurred during file merge.');
      }

      const metadata = parseWorkbookMetadataHeader(response);
      if (metadata) {
        setWorkbookMetadata({
          ...metadata,
          current_dataset: metadata.current_dataset || outputName,
        });
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = outputName || 'merged_output.xlsx';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+?)"/);
        if (match?.[1]) filename = match[1];
      }

      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(downloadUrl);

      if (metadata) {
        setWorkbookMetadata({ ...metadata, current_dataset: filename });
        recordMerge(activeTab, {
          ...metadata,
          suggested_filename: filename,
          source_files: files.map((f) => f.name),
          row_count: 0,
          financial_year: metadata.dealer?.financial_year,
        });
      }

      setSuccessMessage(`Successfully merged ${files.length} files. Output saved as: ${filename}`);
      setWarningModal({ isOpen: false, missingMonths: [] });
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to connect to the backend server. Make sure it is running.');
    } finally {
      setIsMerging(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-zinc-950 dark:text-white">Merge Workbooks</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
          Dealer metadata is extracted automatically from each file&apos;s Read me sheet.
        </p>
      </div>

      {(activeTab === 'gstr1' || activeTab === 'gstr2a') && (
        <div className="relative">
          <DealerHeader compact />
          {isExtracting && (
            <div className="absolute inset-0 bg-white/60 dark:bg-zinc-950/60 rounded-2xl flex items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-3 p-1 bg-zinc-100 dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 max-w-2xl">
        {[
          { id: 'gstr1', label: 'GSTR-1', icon: FileText },
          { id: 'gstr2a', label: 'GSTR-2A', icon: FileText },
          { id: 'eway', label: 'E-Way Bill', icon: Sparkles },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            data-testid={`merge-tab-${id}`}
            onClick={() => setActiveTab(id)}
            className={`py-2 px-4 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center space-x-2 ${
              activeTab === id
                ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-blue-400 shadow-sm border border-zinc-200/50 dark:border-zinc-700/50'
                : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
            }`}
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {error && activeTab !== 'eway' && (
        <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 text-rose-800 dark:text-rose-300 rounded-xl p-4 flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div className="text-sm"><span className="font-semibold">Error:</span> {error}</div>
        </div>
      )}

      {successMessage && activeTab !== 'eway' && (
        <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-400 rounded-xl p-4 flex items-start space-x-3">
          <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div className="text-sm"><span className="font-semibold">Success!</span> {successMessage}</div>
        </div>
      )}

      {activeTab === 'eway' ? (
        <EwayBillSection />
      ) : (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={`lg:col-span-1 space-y-6 ${files.length === 0 ? 'lg:col-span-3 max-w-2xl mx-auto w-full' : ''}`}>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 bg-white dark:bg-zinc-900 ${
              isDragOver
                ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 scale-[0.99] shadow-inner'
                : 'border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 shadow-sm'
            }`}
          >
            <input ref={fileInputRef} type="file" multiple accept=".xlsx,.xls" onChange={handleFileChange} className="hidden" />
            <div className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-100 dark:border-zinc-800 mb-4 text-zinc-500 dark:text-zinc-400">
              <Upload className="h-8 w-8 animate-pulse text-blue-500" />
            </div>
            <h3 className="font-semibold text-zinc-800 dark:text-zinc-200">Drag & drop your files here</h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-[200px]">
              Supports Excel spreadsheets .xlsx and .xls
            </p>
            <button type="button" className="mt-5 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl transition-all shadow-md shadow-blue-500/10">
              Browse Files
            </button>
          </div>

          {files.length > 0 && (
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-4 shadow-sm">
              <h3 className="font-bold text-zinc-950 dark:text-zinc-100 text-sm tracking-wide uppercase">Merge Settings</h3>
              <div>
                <label className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-1.5 block">Output Filename</label>
                <input
                  type="text"
                  value={outputName}
                  onChange={(e) => setOutputName(e.target.value)}
                  className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 text-zinc-950 dark:text-zinc-100"
                />
              </div>
              <button
                type="button"
                onClick={() => triggerMerge(false)}
                disabled={isMerging || isExtracting}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 dark:disabled:bg-zinc-800 text-white font-medium py-3 rounded-xl transition-all flex items-center justify-center space-x-2"
              >
                {isMerging ? <><Loader2 className="h-5 w-5 animate-spin" /><span>Merging Sheets...</span></> : <><Download className="h-5 w-5" /><span>Merge & Download</span></>}
              </button>
            </div>
          )}
        </div>

        {files.length > 0 && (
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-zinc-900 dark:text-zinc-50 text-base">Files to Merge</h3>
                  <span className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs px-2.5 py-0.5 rounded-full font-bold">{files.length}</span>
                </div>
                <button type="button" onClick={clearAllFiles} className="text-xs font-medium text-rose-600 hover:text-rose-700 dark:text-rose-400">Clear All</button>
              </div>

              {(activeTab === 'gstr1' || activeTab === 'gstr2a') && (
                <div className="m-4 p-3 bg-zinc-50 dark:bg-zinc-950/40 rounded-xl border border-zinc-100 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400 flex items-start space-x-2">
                  <HelpCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <div>
                    {activeTab === 'gstr2a' ? (
                      <><span className="font-semibold text-zinc-700 dark:text-zinc-300">GSTR-2A Notice:</span> Files are ordered April → March. Only invoice/note total rows are kept.</>
                    ) : (
                      <><span className="font-semibold text-zinc-700 dark:text-zinc-300">GSTR-1 Order Notice:</span> Files are automatically ordered by Financial Year month sequence (April → March).</>
                    )}
                  </div>
                </div>
              )}

              <div className="divide-y divide-zinc-100 dark:divide-zinc-800 max-h-[420px] overflow-y-auto">
                {files.map((fileEntry, index) => (
                  <div key={fileEntry.id} className="px-5 py-3.5 flex items-center justify-between hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30">
                    <div className="flex items-center space-x-3.5 overflow-hidden pr-4">
                      <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg flex-shrink-0 text-zinc-500 dark:text-zinc-400">
                        <FileSpreadsheet className="h-5 w-5" />
                      </div>
                      <div className="overflow-hidden">
                        <h4 className="font-medium text-sm text-zinc-800 dark:text-zinc-100 truncate" title={fileEntry.name}>{fileEntry.name}</h4>
                        <div className="flex items-center space-x-2 text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                          <span>{formatBytes(fileEntry.size)}</span>
                          {fileEntry.period && (
                            <>
                              <span className="h-1 w-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                              <span className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 rounded font-medium text-blue-700 dark:text-blue-300">{fileEntry.period}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1.5 flex-shrink-0">
                      <button type="button" onClick={() => moveFileUp(index)} disabled={index === 0} className="p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30"><ArrowUp className="h-4 w-4" /></button>
                      <button type="button" onClick={() => moveFileDown(index)} disabled={index === files.length - 1} className="p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30"><ArrowDown className="h-4 w-4" /></button>
                      <button type="button" onClick={() => removeFile(fileEntry.id)} className="p-1.5 rounded-md hover:bg-rose-50 dark:hover:bg-rose-950/30 text-rose-500"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
      )}

      {activeTab !== 'eway' && warningModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center space-x-3 text-amber-600 dark:text-amber-500 mb-4">
              <AlertTriangle className="h-6 w-6 flex-shrink-0" />
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">Missing Months Detected</h3>
            </div>
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">The following financial month(s) are missing between your selected files:</p>
            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200/40 dark:border-amber-900/30 rounded-xl p-4 max-h-[160px] overflow-y-auto mb-6">
              <ul className="space-y-1.5 text-sm text-amber-800 dark:text-amber-300 font-medium">
                {warningModal.missingMonths.map((month) => (
                  <li key={month} className="flex items-center space-x-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                    <span>{month}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex space-x-3">
              <button type="button" onClick={() => setWarningModal({ isOpen: false, missingMonths: [] })} className="flex-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 font-medium py-2.5 rounded-xl text-sm">No, Go Back</button>
              <button type="button" onClick={() => triggerMerge(true)} disabled={isMerging} className="flex-1 bg-amber-600 hover:bg-amber-700 text-white font-medium py-2.5 rounded-xl text-sm">Yes, Merge anyway</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
