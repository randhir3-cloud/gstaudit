import * as comparisonApi from '../api/comparison';

export const comparisonService = {
  runGstr1Eway: comparisonApi.runGstr1EwayComparison,
  fetchComparison: comparisonApi.fetchComparison,
  fetchSummary: comparisonApi.fetchComparisonSummary,
  fetchDetails: comparisonApi.fetchComparisonDetails,
  fetchRisk: comparisonApi.fetchComparisonRisk,
  fetchObservations: comparisonApi.fetchComparisonObservations,
  cacheWorkbook: comparisonApi.cacheWorkbook,
};

export default comparisonService;
