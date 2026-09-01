import * as dashboardApi from '../api/dashboard';

/** Service layer — pages/hooks call services, not raw API modules. */
export const dashboardService = {
  syncSession: dashboardApi.syncSession,
  fetchDashboard: dashboardApi.fetchDashboard,
  fetchMonthCoverage: dashboardApi.fetchMonthCoverage,
  fetchStatistics: dashboardApi.fetchStatistics,
  fetchUploadHistory: dashboardApi.fetchUploadHistory,
  fetchDiscrepancies: dashboardApi.fetchDiscrepancies,
  fetchReadiness: dashboardApi.fetchReadiness,
};

export default dashboardService;
