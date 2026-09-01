import React from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';
import { Icons } from '../../icons';
import { Button } from '../ui/button';

export default function SidebarSection({ items, className, testId = 'app-nav' }) {
  return (
    <nav className={cn('flex flex-wrap gap-2', className)} data-testid={testId} aria-label="Main navigation">
      {items.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              theme.sidebar.item,
              'inline-flex items-center gap-2 px-3 py-1.5 text-sm',
              isActive && theme.sidebar.itemActive,
            )
          }
        >
          <Icon className={Icons.size.sm} aria-hidden />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export function AppBrand({ title, subtitle }) {
  return (
    <div className="flex items-center space-x-3 min-w-0">
      <div className={cn('p-2.5 bg-primary rounded-xl text-primary-foreground shadow-md shrink-0')} aria-hidden>
        <Icons.Spreadsheet className={Icons.size.lg} />
      </div>
      <div className="min-w-0">
        <h1 className={cn(theme.text.heading, 'text-xl md:text-2xl truncate')}>{title}</h1>
        <p className={cn(theme.text.muted, 'text-xs md:text-sm truncate')}>{subtitle}</p>
      </div>
    </div>
  );
}

export function ThemeToggleButton({ themeMode, onToggle }) {
  return (
    <Button
      variant="outline"
      size="icon"
      onClick={onToggle}
      title="Toggle theme"
      aria-label={`Switch to ${themeMode === 'dark' ? 'light' : 'dark'} mode`}
      type="button"
    >
      {themeMode === 'dark' ? <Icons.Sun className={Icons.size.md} /> : <Icons.Moon className={Icons.size.md} />}
    </Button>
  );
}
