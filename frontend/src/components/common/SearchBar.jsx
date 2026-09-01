import React from 'react';
import { cn } from '../../lib/utils';

export default function SearchBar({
  value,
  onChange,
  placeholder = 'Search…',
  className,
  testId = 'search-bar',
  recordCount,
}) {
  return (
    <div className={cn('flex flex-col sm:flex-row gap-2', className)}>
      <input
        type="search"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className="flex-1 text-sm rounded-lg border border-border bg-background px-3 py-2"
        data-testid={testId}
      />
      {recordCount != null && (
        <span className="text-xs text-muted-foreground self-center tabular-nums">{recordCount} records</span>
      )}
    </div>
  );
}
