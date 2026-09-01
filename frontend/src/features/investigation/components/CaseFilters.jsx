import React from 'react';
import { Input } from '../../../components/ui/input';
import theme from '../../../theme/theme';
import { cn } from '../../../lib/utils';
import { FILTER_STATUSES } from '../constants';
import { Icons } from '../../../icons';

export default function CaseFilters({ filters, onChange, loading }) {
  return (
    <div className={cn('flex flex-wrap gap-2 mb-3', theme.text.label)} role="group" aria-label="Case filters">
      <select
        value={filters.status}
        onChange={(e) => onChange({ ...filters, status: e.target.value })}
        className={theme.forms.input}
        data-testid="filter-status"
        aria-label="Filter by status"
      >
        <option value="">All Status</option>
        {FILTER_STATUSES.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <Input
        placeholder="GSTIN"
        value={filters.gstin}
        onChange={(e) => onChange({ ...filters, gstin: e.target.value })}
        className="max-w-[140px]"
        data-testid="filter-gstin"
        aria-label="Filter by GSTIN"
      />
      <Input
        placeholder="Month"
        value={filters.month}
        onChange={(e) => onChange({ ...filters, month: e.target.value })}
        className="max-w-[100px]"
        data-testid="filter-month"
        aria-label="Filter by month"
      />
      {loading && (
        <Icons.Loading className={cn(Icons.size.sm, 'animate-spin self-center text-muted-foreground')} aria-label="Loading cases" />
      )}
    </div>
  );
}
