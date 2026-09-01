export const COMPARISON_DETAIL_LINKS = [
  ['MISSING_IN_GSTR1', 'Missing in GSTR-1'],
  ['MISSING_IN_EWAY', 'Missing in EWB'],
  ['GSTIN_MISMATCH', 'GSTIN Mismatch'],
  ['VALUE_MISMATCH', 'Value Mismatch'],
  ['DATE_MISMATCH', 'Date Mismatch'],
  ['DUPLICATE', 'Duplicates'],
  ['MATCHED', 'Matched'],
];

export function buildComparisonSummaryItems(summary, risk) {
  if (!summary) return [];
  return [
    { label: 'Matched', value: summary.matched_count, testId: 'cmp-matched' },
    { label: 'Missing GSTR-1', value: summary.missing_in_gstr1_count, testId: 'cmp-missing-gstr1' },
    { label: 'Missing EWB', value: summary.missing_in_eway_count, testId: 'cmp-missing-eway' },
    { label: 'GSTIN Mismatch', value: summary.gstin_mismatch_count, testId: 'cmp-gstin' },
    { label: 'Value Mismatch', value: summary.value_mismatch_count, testId: 'cmp-value' },
    { label: 'Date Mismatch', value: summary.date_mismatch_count, testId: 'cmp-date' },
    { label: 'Duplicates', value: summary.duplicate_count, testId: 'cmp-duplicate' },
    {
      label: 'Risk Score',
      value: risk?.overall_risk_score ?? summary.overall_risk_score,
      testId: 'cmp-risk-score',
    },
  ];
}
