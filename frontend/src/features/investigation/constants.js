export const INVESTIGATION_CATEGORIES = [
  { key: 'ALL', label: 'All Cases' },
  { key: 'MISSING_IN_GSTR1', label: 'Missing in GSTR-1' },
  { key: 'MISSING_IN_EWAY', label: 'Missing in EWB' },
  { key: 'GSTIN_MISMATCH', label: 'GSTIN Mismatch' },
  { key: 'DATE_MISMATCH', label: 'Date Mismatch' },
  { key: 'VALUE_MISMATCH', label: 'Value Mismatch' },
  { key: 'DUPLICATE', label: 'Duplicate' },
  { key: 'MULTIPLE_MATCHES', label: 'Multiple Matches' },
  { key: 'HIGH_RISK', label: 'High Risk' },
];

export const CASE_STATUSES = [
  'Pending',
  'Verified',
  'Accepted',
  'Rejected',
  'Needs Clarification',
  'Additional Documents Required',
];

export const FILTER_STATUSES = ['Pending', 'Verified', 'Accepted', 'Rejected'];

export const ATTACHMENT_FIELDS = [
  'notes',
  'reference_number',
  'document_reference',
  'book_page',
  'supporting_evidence',
];
