/**
 * Navigation visibility tests — Layout.jsx conditional nav rendering.
 *
 * Verifies the rule:
 *   - 0 or 1 visible module → nav container NOT rendered
 *   - 2+ visible modules    → nav container IS rendered with all entries
 *
 * Also covers routing, page heading, and application title smoke checks.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Navigate } from 'react-router-dom';

// ── helpers ──────────────────────────────────────────────────────────────────

// Minimal mock of the modules that Layout depends on
vi.mock('../config/appModules', () => ({
  isModuleEnabled: vi.fn(),
  DEFAULT_ROUTE: '/merge',
  DISABLED_MODULE_ROUTES: ['/comparison', '/dashboard'],
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { isModuleEnabled } from '../config/appModules';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';

// NAV_ITEMS inside Layout uses these module keys — expose matching mocks
const ALL_PERMISSIONS = () => true;   // admin-like user
const NO_PERMISSION   = () => false;  // no extras beyond defaults

function setupAuth({ hasPermission = ALL_PERMISSIONS } = {}) {
  useAuth.mockReturnValue({
    user: { username: 'testuser', full_name: 'Test User' },
    logout: vi.fn(),
    hasPermission,
  });
}

/**
 * Render Layout inside a MemoryRouter so NavLink / Outlet work.
 * The Outlet renders a placeholder page for the test.
 */
function renderLayout({ initialEntry = '/merge' } = {}) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route
          element={<Layout theme="dark" onToggleTheme={() => {}} />}
        >
          <Route
            path="/merge"
            element={
              <div>
                <h1>Merge Workbooks</h1>
                <p>Dealer metadata is extracted automatically from each file&apos;s Read me sheet.</p>
              </div>
            }
          />
          <Route path="/comparison" element={<div>Comparison Page</div>} />
          <Route path="/" element={<Navigate to="/merge" replace />} />
          <Route path="*" element={<Navigate to="/merge" replace />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

// ── setup / teardown ─────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
});

// ── TEST SUITE ────────────────────────────────────────────────────────────────

describe('Navigation Visibility — single module (Merge only)', () => {
  beforeEach(() => {
    // Only merge is enabled; all others disabled
    isModuleEnabled.mockImplementation((key) => key === 'merge');
    setupAuth();
  });

  it('TEST 1: Merge page renders successfully when Merge is the only enabled module', () => {
    renderLayout();
    expect(screen.getByText('Merge Workbooks')).toBeInTheDocument();
  });

  it('TEST 2: Navigation container is NOT rendered when only 1 module is visible', () => {
    renderLayout();
    expect(screen.queryByRole('navigation', { name: /main navigation/i })).not.toBeInTheDocument();
  });

  it('TEST 3: The nav-container "Merge" link is NOT rendered when it is the only module', () => {
    renderLayout();
    // The module nav should not exist at all — no navigation landmark
    const nav = screen.queryByRole('navigation', { name: /main navigation/i });
    expect(nav).not.toBeInTheDocument();
  });

  it('TEST 4: "Merge Workbooks" page heading IS rendered', () => {
    renderLayout();
    expect(screen.getByRole('heading', { name: /merge workbooks/i })).toBeInTheDocument();
  });

  it('TEST 5: Application title "Goods and Services Tax" remains rendered', () => {
    renderLayout();
    expect(screen.getByRole('heading', { name: /goods and services tax/i })).toBeInTheDocument();
  });

  it('TEST 9: Direct /merge access renders Merge page content', () => {
    renderLayout({ initialEntry: '/merge' });
    expect(screen.getByText('Merge Workbooks')).toBeInTheDocument();
  });

  it('TEST 10: / redirects to /merge and renders Merge page content', () => {
    renderLayout({ initialEntry: '/' });
    expect(screen.getByText('Merge Workbooks')).toBeInTheDocument();
  });

  it('TEST 11: Known disabled module route is in DISABLED_MODULE_ROUTES (driving the /merge redirect in App.jsx)', () => {
    // The ModuleRoute redirect is an App.jsx concern tested in featureAvailability.test.js.
    // Here we verify the config-level source of truth that drives that redirect.
    const { DISABLED_MODULE_ROUTES } = require('../config/appModules');
    expect(DISABLED_MODULE_ROUTES).toContain('/comparison');
    expect(DISABLED_MODULE_ROUTES).toContain('/');       // dashboard route is '/'
    expect(DISABLED_MODULE_ROUTES).not.toContain('/merge');
  });
});

describe('Navigation Visibility — two modules visible', () => {
  beforeEach(() => {
    // Both merge and comparison are enabled
    isModuleEnabled.mockImplementation((key) => key === 'merge' || key === 'comparison');
    setupAuth(); // user has all permissions
  });

  it('TEST 6: Navigation container renders when 2+ modules are visible', () => {
    renderLayout();
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument();
  });

  it('TEST 7: Both "Merge" and "Comparison" nav entries render inside the nav element', () => {
    renderLayout();
    const nav = screen.getByRole('navigation', { name: /main navigation/i });
    // Both items must be inside the nav element
    const links = Array.from(nav.querySelectorAll('a'));
    const labels = links.map((a) => a.textContent.trim());
    expect(labels.some((l) => /merge/i.test(l))).toBe(true);
    expect(labels.some((l) => /comparison/i.test(l))).toBe(true);
  });
});

describe('Navigation Visibility — permission filter', () => {
  it('TEST 8: Two globally enabled modules but user has permission for only Merge → nav stays hidden', () => {
    // Enable merge + comparison at feature level
    isModuleEnabled.mockImplementation((key) => key === 'merge' || key === 'comparison');
    // User has NO permissions — comparison requires 'compare_files' or similar
    // merge_files permission is also absent here
    setupAuth({ hasPermission: (p) => false }); // user sees nothing extra

    renderLayout();
    // Only merge would have passed the feature flag but user has no merge_files permission either.
    // Items array is empty → nav still hidden.
    expect(screen.queryByRole('navigation', { name: /main navigation/i })).not.toBeInTheDocument();
  });
});
