/** Sidebar / navigation tokens. */
export const sidebarWidth = 'w-64';
export const sidebarCollapsedWidth = 'w-16';

export const sidebarShell =
  'flex flex-col border-r border-border bg-sidebar text-sidebar-foreground';

export const sidebarItem =
  'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium '
  + 'text-muted-foreground hover:bg-hover hover:text-foreground transition-colors';

export const sidebarItemActive =
  'bg-selected text-primary font-semibold';

export const sidebarSection =
  'px-3 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground';

export const sidebar = {
  width: sidebarWidth,
  collapsedWidth: sidebarCollapsedWidth,
  shell: sidebarShell,
  item: sidebarItem,
  itemActive: sidebarItemActive,
  section: sidebarSection,
};

export default sidebar;
