import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { cn } from '../lib/utils';
import theme from '../theme/theme';
import { Icons } from '../icons';
import SidebarSection, { AppBrand, ThemeToggleButton } from './layout/SidebarSection';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { isModuleEnabled } from '../config/appModules';

// All top-level navigation items. Items with enabled === false via isModuleEnabled()
// are automatically hidden. To expose a module, update src/config/appModules.js.
const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: Icons.Dashboard, end: true, moduleKey: 'dashboard' },
  { to: '/merge', label: 'Merge', icon: Icons.Files, permission: 'merge_files', moduleKey: 'merge' },
  { to: '/workbook', label: 'Workbook Viewer', icon: Icons.Table, moduleKey: 'workbookViewer' },
  { to: '/comparison', label: 'Comparison', icon: Icons.Compare, moduleKey: 'comparison' },
  { to: '/investigation', label: 'Investigation', icon: Icons.Investigate, permission: 'update_cases', moduleKey: 'investigation' },
  { to: '/audit-intelligence', label: 'Audit Intelligence', icon: Icons.Sparkles, permission: 'view_intelligence', moduleKey: 'auditIntelligence' },
  { to: '/audit-cases', label: 'Case Management', icon: Icons.Shield, permission: 'manage_audit_cases', moduleKey: 'caseManagement' },
  { to: '/officer-tasks', label: 'Officer Tasks', icon: Icons.Calendar, permission: 'manage_audit_cases', moduleKey: 'officerTasks' },
  { to: '/supervisor-dashboard', label: 'Supervisor', icon: Icons.Users, permission: 'supervise_audit_cases', moduleKey: 'supervisor' },
  { to: '/audit-report', label: 'Audit Report', icon: Icons.Report, permission: 'view_reports', moduleKey: 'auditReport' },
  { to: '/admin', label: 'Administration', icon: Icons.Shield, permission: 'view_admin', moduleKey: 'administration' },
  { to: '/system-monitor', label: 'System Monitor', icon: Icons.Activity, permission: 'view_system_monitor', moduleKey: 'systemMonitor' },
];

export default function Layout({ theme: themeMode, onToggleTheme }) {
  const { user, logout, hasPermission } = useAuth();

  // Step 1: filter by feature flag (module enabled in appModules.js)
  // Step 2: filter by user permission (existing authorization — unchanged)
  const items = NAV_ITEMS.filter(
    (item) => isModuleEnabled(item.moduleKey) && (!item.permission || hasPermission(item.permission)),
  );

  return (
    <div className={cn('min-h-screen bg-background text-foreground flex flex-col', theme.transition.theme)}>
      <header className={cn('border-b border-border bg-card/50 backdrop-blur-md sticky top-0 z-sticky')}>
        <div className={cn(theme.layout.pageShell, 'py-4 flex items-center justify-between gap-4')}>
          <AppBrand title="Goods and Services Tax" subtitle="Excel Merger for GST Audit" />
          <div className="flex items-center gap-3">
            {user && (
              <span className="text-xs text-muted-foreground hidden sm:inline" data-testid="layout-user">{user.full_name || user.username}</span>
            )}
            {user && (
              <Button variant="outline" size="sm" onClick={() => logout()} data-testid="logout-button">Logout</Button>
            )}
            <ThemeToggleButton themeMode={themeMode} onToggle={onToggleTheme} />
          </div>
        </div>
        {/* Module navigation — hidden when the user has only 1 visible destination.
            A single-item nav provides no useful navigation and creates empty spacing.
            Automatically reappears when 2+ modules are enabled and user-accessible. */}
        {items.length >= 2 && (
          <div className={cn(theme.layout.pageShell, 'pb-3')}>
            <SidebarSection items={items} />
          </div>
        )}
      </header>

      <main className={cn('flex-1 w-full mx-auto', theme.layout.pageMaxWidth, theme.spacing.page)}>
        <Outlet />
      </main>

      <footer className={cn('border-t border-border py-6 bg-card text-center text-xs text-muted-foreground mt-auto')}>
        <div className={cn(theme.layout.pageShell, 'space-y-1')}>
          <p>Excel Merger for GST Audit • Built by Randhir Singh</p>
          <p>
            For any query, send email to{' '}
            <a href="mailto:randhirsandhu81@gmail.com" className="text-primary hover:underline">
              randhirsandhu81@gmail.com
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
