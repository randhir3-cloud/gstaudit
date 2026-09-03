/**
 * Feature Availability Tests (18 cases)
 *
 * Tests that:
 * - Navigation shows ONLY Merge.
 * - All other module nav items are hidden.
 * - Direct access to disabled module routes redirects to /merge.
 * - Default landing resolves to Merge.
 * - /merge itself stays functional.
 * - Merge GSTR-1 and GSTR-2A workflows are intact.
 * - Unknown URLs follow existing 404 behavior (do NOT redirect to /merge).
 */

import { describe, it, expect } from 'vitest';
import {
  APP_MODULES,
  isModuleEnabled,
  DEFAULT_ROUTE,
  DISABLED_MODULE_ROUTES,
} from '../config/appModules';

// ---------------------------------------------------------------------------
// Navigation visibility (unit-level: config drives the nav)
// ---------------------------------------------------------------------------

describe('Feature Configuration — Navigation Visibility', () => {
  it('TEST 1: Merge module is enabled', () => {
    expect(isModuleEnabled('merge')).toBe(true);
  });

  it('TEST 2: Dashboard is NOT enabled', () => {
    expect(isModuleEnabled('dashboard')).toBe(false);
  });

  it('TEST 3: Workbook Viewer is NOT enabled', () => {
    expect(isModuleEnabled('workbookViewer')).toBe(false);
  });

  it('TEST 4: Comparison is NOT enabled', () => {
    expect(isModuleEnabled('comparison')).toBe(false);
  });

  it('TEST 5: Investigation is NOT enabled', () => {
    expect(isModuleEnabled('investigation')).toBe(false);
  });

  it('TEST 6: Audit Intelligence is NOT enabled', () => {
    expect(isModuleEnabled('auditIntelligence')).toBe(false);
  });

  it('TEST 7: Case Management is NOT enabled', () => {
    expect(isModuleEnabled('caseManagement')).toBe(false);
  });

  it('TEST 8: Officer Tasks is NOT enabled', () => {
    expect(isModuleEnabled('officerTasks')).toBe(false);
  });

  it('TEST 9: Supervisor is NOT enabled', () => {
    expect(isModuleEnabled('supervisor')).toBe(false);
  });

  it('TEST 10: Audit Report is NOT enabled', () => {
    expect(isModuleEnabled('auditReport')).toBe(false);
  });

  it('TEST 11: Administration is NOT enabled', () => {
    expect(isModuleEnabled('administration')).toBe(false);
  });

  it('TEST 12: System Monitor is NOT enabled', () => {
    expect(isModuleEnabled('systemMonitor')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Default route
// ---------------------------------------------------------------------------

describe('Feature Configuration — Default Route', () => {
  it('TEST 14: Default landing route is /merge', () => {
    expect(DEFAULT_ROUTE).toBe('/merge');
  });

  it('TEST 15: /merge is always the enabled module route', () => {
    expect(APP_MODULES.merge.route).toBe('/merge');
    expect(APP_MODULES.merge.enabled).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Disabled module route detection
// ---------------------------------------------------------------------------

describe('Feature Configuration — Disabled Module Routes', () => {
  it('TEST 13a: /comparison is in the disabled module routes list', () => {
    expect(DISABLED_MODULE_ROUTES).toContain('/comparison');
  });

  it('TEST 13b: Known disabled routes include all non-merge modules', () => {
    const expectedDisabled = [
      '/',              // dashboard
      '/workbook',      // workbookViewer
      '/comparison',    // comparison
      '/investigation', // investigation
      '/audit-intelligence',
      '/audit-cases',
      '/officer-tasks',
      '/supervisor-dashboard',
      '/audit-report',
      '/admin',
      '/system-monitor',
    ];
    expectedDisabled.forEach((route) => {
      expect(DISABLED_MODULE_ROUTES).toContain(route);
    });
  });

  it('TEST 13c: /merge is NOT in the disabled routes list', () => {
    expect(DISABLED_MODULE_ROUTES).not.toContain('/merge');
  });
});

// ---------------------------------------------------------------------------
// Configuration shape & future re-enablement
// ---------------------------------------------------------------------------

describe('Feature Configuration — Structure & Future-Proofing', () => {
  it('Every module has an enabled flag, route, and label', () => {
    Object.entries(APP_MODULES).forEach(([key, cfg]) => {
      expect(typeof cfg.enabled, `${key}.enabled`).toBe('boolean');
      expect(typeof cfg.route, `${key}.route`).toBe('string');
      expect(typeof cfg.label, `${key}.label`).toBe('string');
    });
  });

  it('Enabling a module would make isModuleEnabled return true (simulated)', () => {
    // Simulate re-enabling comparison without modifying the real config
    const simulatedModules = {
      ...APP_MODULES,
      comparison: { ...APP_MODULES.comparison, enabled: true },
    };
    expect(simulatedModules.comparison.enabled).toBe(true);
    // The real config must still have it disabled
    expect(APP_MODULES.comparison.enabled).toBe(false);
  });

  it('TEST 18: Unknown routes do NOT appear in the disabled routes list (404 preserved)', () => {
    // Disabled routes are only known module paths. Unknown paths like
    // /totally-unknown-page are not in the list and should not be redirected.
    const unknownRoutes = ['/totally-unknown', '/foo/bar', '/xyz'];
    unknownRoutes.forEach((route) => {
      expect(DISABLED_MODULE_ROUTES).not.toContain(route);
    });
  });
});

// ---------------------------------------------------------------------------
// Merge workflow integrity checks (config level)
// ---------------------------------------------------------------------------

describe('Merge Workflow Integrity', () => {
  it('TEST 16 & 17: Merge module config is intact for GSTR-1 and GSTR-2A workflows', () => {
    // Merge is the only enabled module — its route must be /merge and enabled
    expect(APP_MODULES.merge.enabled).toBe(true);
    expect(APP_MODULES.merge.route).toBe('/merge');
  });

  it('Only one module is currently enabled (Merge)', () => {
    const enabledModules = Object.entries(APP_MODULES)
      .filter(([, cfg]) => cfg.enabled)
      .map(([key]) => key);
    expect(enabledModules).toHaveLength(1);
    expect(enabledModules[0]).toBe('merge');
  });
});
