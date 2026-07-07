import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  FileSpreadsheet, 
  Trash2, 
  Loader2, 
  Sun, 
  Moon, 
  ArrowUp, 
  ArrowDown, 
  Download, 
  AlertTriangle, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  HelpCircle,
  Sparkles
} from 'lucide-react';

// The API base URL is now empty (relative) because Nginx/Vite will proxy `/api` requests
const API_BASE_URL = '';

function App() {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') || 'dark';
    }
    return 'dark';
  });

  const [activeTab, setActiveTab] = useState('gstr1'); // 'eway' or 'gstr1'
  const [files, setFiles] = useState([]); // Array of { id, file, name, size, period (for gstr1) }
  const [outputName, setOutputName] = useState('');
  const [isMerging, setIsMerging] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  
  // Warning modal for missing months in GSTR-1
  const [warningModal, setWarningModal] = useState({ isOpen: false, missingMonths: [] });

  const fileInputRef = useRef(null);

  // Apply dark mode class
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Set default output name based on tab and files
  useEffect(() => {
    if (activeTab === 'eway') {
      setOutputName('eway_merged_output.xlsx');
    } else {
      // Try to determine output name pattern like GSTR1_{GSTIN}_{FY}_Merged.xlsx
      // We will let the API handle the name generation, but we can set a placeholder
      setOutputName('GSTR1_Merged.xlsx');
    }
    setFiles([]);
    setError(null);
    setSuccessMessage(null);
  }, [activeTab]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Helper: Format bytes
  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  // Helper: Extract GSTR1 period from filename
  const extractPeriodFromFilename = (name) => {
    const match = name.match(/_(\d{2})(\d{4})_/);
    if (match) {
      const monthMap = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
      };
      return `${monthMap[match[1]] || match[1]}-${match[2]}`;
    }
    return 'Unknown Period';
  };

  // Sort helper for GSTR-1 files based on Indian Financial Year (April -> March)
  const getFYMonthSortKey = (name) => {
    const match = name.match(/_(\d{2})(\d{4})_/);
    if (match) {
      const mm = parseInt(match[1], 10);
      const yyyy = parseInt(match[2], 10);
      if (mm >= 4) {
        return yyyy * 100 + (mm - 3); // Apr=1 ... Dec=9
      } else {
        return (yyyy - 1) * 100 + (mm + 9); // Jan=10 ... Mar=12
      }
    }
    return 999999;
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    addFilesToList(selectedFiles);
  };

  const addFilesToList = (selectedFiles) => {
    setError(null);
    setSuccessMessage(null);
    
    // Filter Excel files
    const validFiles = selectedFiles.filter(file => {
      const name = file.name.toLowerCase();
      return name.endsWith('.xlsx') || name.endsWith('.xls');
    });

    if (validFiles.length === 0) {
      setError("Please select valid Excel files (.xlsx or .xls).");
      return;
    }

    const newFiles = validFiles.map((file, index) => {
      const period = activeTab === 'gstr1' ? extractPeriodFromFilename(file.name) : null;
      return {
        id: `file_${Date.now()}_${index}_${Math.random().toString(36).substr(2, 5)}`,
        file,
        name: file.name,
        size: file.size,
        period
      };
    });

    setFiles(prev => {
      const combined = [...prev, ...newFiles];
      
      // Auto sort GSTR-1 files in Financial Year order upon upload
      if (activeTab === 'gstr1') {
        combined.sort((a, b) => getFYMonthSortKey(a.name) - getFYMonthSortKey(b.name));
      }
      return combined;
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeFile = (id) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const clearAllFiles = () => {
    setFiles([]);
    setError(null);
    setSuccessMessage(null);
  };

  // Reordering helpers
  const moveFileUp = (index) => {
    if (index === 0) return;
    setFiles(prev => {
      const copy = [...prev];
      const temp = copy[index];
      copy[index] = copy[index - 1];
      copy[index - 1] = temp;
      return copy;
    });
  };

  const moveFileDown = (index) => {
    setFiles(prev => {
      if (index === prev.length - 1) return prev;
      const copy = [...prev];
      const temp = copy[index];
      copy[index] = copy[index + 1];
      copy[index + 1] = temp;
      return copy;
    });
  };

  // Drag and drop event handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) {
      addFilesToList(Array.from(e.dataTransfer.files));
    }
  };

  // Trigger file merge API call
  const triggerMerge = async (ignoreMissing = false) => {
    if (files.length === 0) {
      setError("Please add some Excel files first.");
      return;
    }

    setIsMerging(true);
    setError(null);
    setSuccessMessage(null);

    const formData = new FormData();
    files.forEach(f => {
      formData.append('files', f.file);
    });

    const endpoint = activeTab === 'eway' ? '/api/merge/eway' : '/api/merge/gstr1';
    const queryParam = activeTab === 'gstr1' ? `?ignore_missing=${ignoreMissing}` : '';

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}${queryParam}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        
        // Handle GSTR-1 Missing Months Warning
        if (activeTab === 'gstr1' && errorData.error_type === 'missing_months') {
          setWarningModal({
            isOpen: true,
            missingMonths: errorData.missing
          });
          setIsMerging(false);
          return;
        }

        throw new Error(errorData.detail || "An error occurred during file merge.");
      }

      // Successful merge -> Trigger file download
      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = outputName || 'merged_output.xlsx';

      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+?)"/);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(downloadUrl);

      setSuccessMessage(`Successfully merged ${files.length} files. Output saved as: ${filename}`);
      setWarningModal({ isOpen: false, missingMonths: [] });
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to connect to the backend server. Make sure it is running.");
    } finally {
      setIsMerging(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50 flex flex-col transition-colors duration-300">
      
      {/* HEADER SECTION */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-600 rounded-xl text-white shadow-lg shadow-blue-500/20">
              <FileSpreadsheet className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-zinc-950 dark:text-white flex items-center">
                Excel Merger <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300">Web</span>
              </h1>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">GST Excel & E-Way Bill Utility</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all border border-zinc-200 dark:border-zinc-700"
              title="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 md:p-8 space-y-6">
        
        {/* TABS SELECTOR */}
        <div className="grid grid-cols-2 p-1 bg-zinc-100 dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 max-w-md mx-auto">
          <button
            onClick={() => setActiveTab('gstr1')}
            className={`py-2 px-4 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center space-x-2 ${
              activeTab === 'gstr1'
                ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-blue-400 shadow-sm border border-zinc-200/50 dark:border-zinc-700/50'
                : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
            }`}
          >
            <FileText className="h-4 w-4" />
            <span>GSTR-1 Merge</span>
          </button>
          <button
            onClick={() => setActiveTab('eway')}
            className={`py-2 px-4 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center space-x-2 ${
              activeTab === 'eway'
                ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-blue-400 shadow-sm border border-zinc-200/50 dark:border-zinc-700/50'
                : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'
            }`}
          >
            <Sparkles className="h-4 w-4" />
            <span>E-Way Bill Merge</span>
          </button>
        </div>

        {/* ALERTS */}
        {error && (
          <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 text-rose-800 dark:text-rose-300 rounded-xl p-4 flex items-start space-x-3 animate-fade-in shadow-sm">
            <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <span className="font-semibold">Error:</span> {error}
            </div>
          </div>
        )}

        {successMessage && (
          <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-400 rounded-xl p-4 flex items-start space-x-3 animate-fade-in shadow-sm">
            <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <span className="font-semibold">Success!</span> {successMessage}
            </div>
          </div>
        )}

        {/* WORKSPACE LAYOUT */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* UPLOAD & CONTROLS - LEFT 1/3 (or full if no files) */}
          <div className={`lg:col-span-1 space-y-6 ${files.length === 0 ? 'lg:col-span-3 max-w-2xl mx-auto w-full' : ''}`}>
            
            {/* DROP ZONE */}
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
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-100 dark:border-zinc-800 mb-4 text-zinc-500 dark:text-zinc-400">
                <Upload className="h-8 w-8 animate-pulse text-blue-500" />
              </div>
              <h3 className="font-semibold text-zinc-800 dark:text-zinc-200">Drag & drop your files here</h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-[200px]">
                Supports Excel spreadsheets <span className="font-mono bg-zinc-100 dark:bg-zinc-800 px-1 rounded">.xlsx</span> and <span className="font-mono bg-zinc-100 dark:bg-zinc-800 px-1 rounded">.xls</span>
              </p>
              <button 
                type="button"
                className="mt-5 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl transition-all shadow-md shadow-blue-500/10"
              >
                Browse Files
              </button>
            </div>

            {/* MERGE SETTINGS */}
            {files.length > 0 && (
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-4 shadow-sm">
                <h3 className="font-bold text-zinc-950 dark:text-zinc-100 text-sm tracking-wide uppercase">Merge Settings</h3>
                
                <div>
                  <label className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 mb-1.5 block">
                    Output Filename
                  </label>
                  <input
                    type="text"
                    value={outputName}
                    onChange={(e) => setOutputName(e.target.value)}
                    placeholder="Enter file name"
                    className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 text-zinc-950 dark:text-zinc-100"
                  />
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => triggerMerge(false)}
                    disabled={isMerging}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 dark:disabled:bg-zinc-800 disabled:text-zinc-500 dark:disabled:text-zinc-600 text-white font-medium py-3 rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/10 cursor-pointer disabled:cursor-not-allowed"
                  >
                    {isMerging ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span>Merging Sheets...</span>
                      </>
                    ) : (
                      <>
                        <Download className="h-5 w-5" />
                        <span>Merge & Download</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* FILE LIST & DETAILS - RIGHT 2/3 */}
          {files.length > 0 && (
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden">
                
                {/* LIST HEADER */}
                <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-bold text-zinc-900 dark:text-zinc-50 text-base">Files to Merge</h3>
                    <span className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs px-2.5 py-0.5 rounded-full font-bold">
                      {files.length}
                    </span>
                  </div>
                  <button
                    onClick={clearAllFiles}
                    className="text-xs font-medium text-rose-600 hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300 transition-colors"
                  >
                    Clear All
                  </button>
                </div>

                {/* INSTRUCTION NOTE */}
                {activeTab === 'gstr1' && (
                  <div className="m-4 p-3 bg-zinc-50 dark:bg-zinc-950/40 rounded-xl border border-zinc-100 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400 flex items-start space-x-2">
                    <HelpCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-semibold text-zinc-700 dark:text-zinc-300">GSTR-1 Order Notice:</span> Files are automatically ordered by their Financial Year month sequence (April → March). You can adjust this sequence using the Up/Down buttons if needed.
                    </div>
                  </div>
                )}

                {/* LIST OF FILES */}
                <div className="divide-y divide-zinc-100 dark:divide-zinc-800 max-h-[420px] overflow-y-auto">
                  {files.map((fileEntry, index) => (
                    <div 
                      key={fileEntry.id} 
                      className="px-5 py-3.5 flex items-center justify-between hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30 transition-colors duration-150"
                    >
                      <div className="flex items-center space-x-3.5 overflow-hidden pr-4">
                        <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg flex-shrink-0 text-zinc-500 dark:text-zinc-400">
                          <FileSpreadsheet className="h-5 w-5" />
                        </div>
                        <div className="overflow-hidden">
                          <h4 className="font-medium text-sm text-zinc-800 dark:text-zinc-100 truncate" title={fileEntry.name}>
                            {fileEntry.name}
                          </h4>
                          <div className="flex items-center space-x-2 text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                            <span>{formatBytes(fileEntry.size)}</span>
                            {fileEntry.period && (
                              <>
                                <span className="h-1 w-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                                <span className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 rounded font-medium text-blue-700 dark:text-blue-300">
                                  {fileEntry.period}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* CONTROLS */}
                      <div className="flex items-center space-x-1.5 flex-shrink-0">
                        <button
                          onClick={() => moveFileUp(index)}
                          disabled={index === 0}
                          className="p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30 text-zinc-500 dark:text-zinc-400 transition-colors"
                          title="Move Up"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => moveFileDown(index)}
                          disabled={index === files.length - 1}
                          className="p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-30 text-zinc-500 dark:text-zinc-400 transition-colors"
                          title="Move Down"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => removeFile(fileEntry.id)}
                          className="p-1.5 rounded-md hover:bg-rose-50 dark:hover:bg-rose-950/30 text-rose-500 dark:text-rose-400 transition-colors"
                          title="Remove File"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

              </div>
            </div>
          )}

        </div>

      </main>

      {/* FOOTER */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-6 bg-white dark:bg-zinc-950 text-center text-xs text-zinc-400 dark:text-zinc-500 mt-auto">
        <p className="max-w-5xl mx-auto px-6">
          Excel Merger Web App • Built by Randhir Singh
        </p>
      </footer>

      {/* WARNING MODAL FOR MISSING MONTHS */}
      {warningModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl w-full max-w-md p-6 overflow-hidden animate-fade-in">
            <div className="flex items-center space-x-3 text-amber-600 dark:text-amber-500 mb-4">
              <AlertTriangle className="h-6 w-6 flex-shrink-0" />
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">Missing Months Detected</h3>
            </div>
            
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">
              The following financial month(s) are missing between your selected files:
            </p>

            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200/40 dark:border-amber-900/30 rounded-xl p-4 max-h-[160px] overflow-y-auto mb-6">
              <ul className="space-y-1.5 text-sm text-amber-800 dark:text-amber-300 font-medium">
                {warningModal.missingMonths.map((month, idx) => (
                  <li key={idx} className="flex items-center space-x-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                    <span>{month}</span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-6">
              Do you want to continue merging without the missing file(s)? 
              Selecting "Yes" will merge the existing months.
            </p>

            <div className="flex space-x-3">
              <button
                onClick={() => setWarningModal({ isOpen: false, missingMonths: [] })}
                className="flex-1 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 font-medium py-2.5 rounded-xl text-sm transition-all border border-zinc-200 dark:border-zinc-700"
              >
                No, Go Back
              </button>
              <button
                onClick={() => triggerMerge(true)}
                disabled={isMerging}
                className="flex-1 bg-amber-600 hover:bg-amber-700 disabled:bg-zinc-300 dark:disabled:bg-zinc-800 text-white font-medium py-2.5 rounded-xl text-sm transition-all flex items-center justify-center space-x-2 shadow-md shadow-amber-600/10"
              >
                {isMerging ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <span>Yes, Merge anyway</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
