/**
 * Centralized Application Module Feature Configuration
 *
 * Controls which top-level modules are currently enabled for user access.
 *
 * USAGE:
 *   - Navigation renders only modules with enabled === true.
 *   - Routes for disabled modules redirect to /merge.
 *   - To re-enable a module later, simply set its enabled flag to true.
 *
 * NOTE: Disabling a module here affects ONLY user-facing navigation and route
 * access. It does NOT delete or comment out any source code. All pages,
 * components, services, and tests for disabled modules are fully preserved.
 */

export const APP_MODULES = {
  merge: {
    enabled: true,
    route: '/merge',
    label: 'Merge',
  },
  dashboard: {
    enabled: false,
    route: '/',
    label: 'Dashboard',
  },
  workbookViewer: {
    enabled: false,
    route: '/workbook',
    label: 'Workbook Viewer',
  },
  comparison: {
    enabled: false,
    route: '/comparison',
    label: 'Comparison',
  },
  investigation: {
    enabled: false,
    route: '/investigation',
    label: 'Investigation',
  },
  auditIntelligence: {
    enabled: false,
    route: '/audit-intelligence',
    label: 'Audit Intelligence',
  },
  caseManagement: {
    enabled: false,
    route: '/audit-cases',
    label: 'Case Management',
  },
  officerTasks: {
    enabled: false,
    route: '/officer-tasks',
    label: 'Officer Tasks',
  },
  supervisor: {
    enabled: false,
    route: '/supervisor-dashboard',
    label: 'Supervisor',
  },
  auditReport: {
    enabled: false,
    route: '/audit-report',
    label: 'Audit Report',
  },
  administration: {
    enabled: false,
    route: '/admin',
    label: 'Administration',
  },
  systemMonitor: {
    enabled: false,
    route: '/system-monitor',
    label: 'System Monitor',
  },
};

/**
 * Returns true if the given module key is currently enabled.
 * @param {keyof typeof APP_MODULES} moduleKey
 * @returns {boolean}
 */
export function isModuleEnabled(moduleKey) {
  return APP_MODULES[moduleKey]?.enabled === true;
}

/**
 * The application's default landing route.
 * Points to the first enabled module (merge for now).
 */
export const DEFAULT_ROUTE = '/merge';

/**
 * Set of routes belonging to known-but-disabled modules.
 * Used by the router to distinguish "disabled known route" from "unknown 404".
 */
export const DISABLED_MODULE_ROUTES = Object.values(APP_MODULES)
  .filter((m) => !m.enabled)
  .map((m) => m.route);
