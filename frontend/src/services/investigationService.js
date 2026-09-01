import * as investigationApi from '../api/investigation';

export const investigationService = {
  fetchCases: investigationApi.fetchInvestigation,
  fetchCase: investigationApi.fetchCase,
  updateCase: investigationApi.updateCase,
  bulkUpdate: investigationApi.bulkUpdateCases,
  previewReport: investigationApi.fetchReportPreview,
  generateReport: investigationApi.generateReport,
};

export default investigationService;
