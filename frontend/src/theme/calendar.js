/** FY calendar cell status — semantic Tailwind classes */
export const calendarCellStatus = {
  uploaded: 'bg-success/10 text-success border-success/30',
  missing: 'bg-muted text-muted-foreground border-border',
  duplicate: 'bg-warning/10 text-warning border-warning/30',
  processing: 'bg-info/10 text-info border-info/30',
};

export const calendarShell = 'rounded-2xl border border-border bg-card overflow-hidden';
export const calendarLegend = 'flex flex-wrap gap-4 px-4 py-3 text-xs text-muted-foreground border-t border-border bg-muted/50';
export const calendarHeaderCell = 'sticky bg-table-header px-3 py-3 font-bold text-foreground border-b border-r border-border';
export const calendarRowHeader = 'sticky left-0 z-10 bg-card px-3 py-2 font-semibold text-foreground border-r border-border whitespace-nowrap';
export const calendarMonthCell = 'w-full min-w-[72px] sm:min-w-[88px] rounded-lg border px-1.5 py-2 text-center transition hover:ring-2 hover:ring-primary focus:outline-none focus:ring-2 focus:ring-primary';

export const calendar = {
  cellStatus: calendarCellStatus,
  shell: calendarShell,
  legend: calendarLegend,
  headerCell: calendarHeaderCell,
  rowHeader: calendarRowHeader,
  monthCell: calendarMonthCell,
};

export default calendar;
