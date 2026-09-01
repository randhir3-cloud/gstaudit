/** Chart palette for dashboards and intelligence heatmaps (future). */
export const chartSeries = [
  'hsl(var(--primary))',
  'hsl(var(--success))',
  'hsl(var(--warning))',
  'hsl(var(--danger))',
  'hsl(var(--info))',
  'hsl(262 83% 58%)',
  'hsl(173 58% 39%)',
];

export const chartGrid = 'stroke-border';
export const chartAxis = 'text-muted-foreground text-xs';
export const chartTooltip = 'bg-card border border-border rounded-lg shadow-md p-2 text-sm';

export const riskHeatmap = {
  low: 'hsl(142 76% 36%)',
  medium: 'hsl(38 92% 50%)',
  high: 'hsl(25 95% 53%)',
  critical: 'hsl(0 84% 60%)',
};

export const charts = {
  series: chartSeries,
  grid: chartGrid,
  axis: chartAxis,
  tooltip: chartTooltip,
  riskHeatmap,
};

export default charts;
