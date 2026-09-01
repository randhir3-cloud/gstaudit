/**
 * @typedef {Object} DealerMetadata
 * @property {string} [id]
 * @property {string} gstin
 * @property {string} legal_name
 * @property {string} trade_name
 * @property {string} financial_year
 * @property {string} tax_period
 * @property {string} arn
 * @property {string} arn_date
 * @property {string} download_date
 */

/**
 * @typedef {Object} WorkbookMetadata
 * @property {string} workbook_id
 * @property {DealerMetadata} dealer
 * @property {string} return_type
 * @property {string[]} source_files
 * @property {string} current_dataset
 */

export const EMPTY_DEALER = {
  gstin: '',
  legal_name: '',
  trade_name: '',
  financial_year: '',
  tax_period: '',
  arn: '',
  arn_date: '',
  download_date: '',
};

export function dealerDisplayName(dealer) {
  return dealer?.legal_name || dealer?.trade_name || dealer?.gstin || 'No dealer loaded';
}
