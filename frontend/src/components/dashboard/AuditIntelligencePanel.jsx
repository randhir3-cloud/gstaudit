import React from 'react';
import { Link } from 'react-router-dom';
import ContentCard from '../cards/ContentCard';
import RiskCard from '../cards/RiskCard';
import ResponsiveGrid from '../layout/ResponsiveGrid';
import { Icons } from '../../icons';
import theme from '../../theme/theme';
import { cn } from '../../lib/utils';
import PriorityBadge from '../badges/PriorityBadge';

function HeatmapGrid({ title, cells, testId }) {
  if (!cells?.length) return null;
  const maxRisk = Math.max(...cells.map((c) => c.risk_score || 0), 1);
  return (
    <div data-testid={testId}>
      <h4 className={cn(theme.text.label, 'font-semibold mb-2')}>{title}</h4>
      <div className="flex flex-wrap gap-1.5">
        {cells.slice(0, 8).map((cell) => {
          const intensity = Math.round((cell.risk_score / maxRisk) * 100);
          return (
            <div
              key={cell.label}
              className="rounded-lg px-2 py-1 text-[10px] border border-border"
              style={{ backgroundColor: `rgba(239, 68, 68, ${intensity / 200})` }}
              title={`${cell.label}: ${cell.count} issues, risk ${cell.risk_score}`}
            >
              <span className="font-medium">{cell.label.slice(0, 12)}</span>
              <span className={cn('ml-1 tabular-nums', theme.text.muted)}>{cell.count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function AuditIntelligencePanel({ intelligence }) {
  if (!intelligence?.cards) return null;
  const { cards, patterns, heatmaps, executive_insights: insights } = intelligence;
  const hasData = cards.high_risk_cases > 0 || patterns?.length > 0;
  if (!hasData) return null;

  const currency = cards.largest_tax_difference?.toLocaleString?.('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  });

  return (
    <ContentCard
      testId="audit-intelligence-panel"
      title="Audit Intelligence"
      description="Automated risk analysis and investigation priorities"
      actions={<Link to="/audit-intelligence" className="text-xs text-primary font-medium">Audit Intelligence →</Link>}
    >
      <ResponsiveGrid columns="six" className="mb-5">
        <RiskCard label="High Risk Cases" value={cards.high_risk_cases} testId="intel-high-risk-cases" icon={Icons.Warning} highlight={cards.high_risk_cases > 0} />
        <RiskCard label="Critical Suppliers" value={cards.critical_suppliers} testId="intel-critical-suppliers" icon={Icons.Building} />
        <RiskCard label="Critical Customers" value={cards.critical_customers} testId="intel-critical-customers" icon={Icons.Users} />
        <RiskCard label="Largest Tax Diff" value={currency} testId="intel-largest-tax-diff" icon={Icons.Currency} highlight />
        <RiskCard label="Highest Risk Month" value={cards.highest_risk_month || '—'} testId="intel-highest-risk-month" icon={Icons.Calendar} />
        <RiskCard label="Open Cases" value={cards.open_investigation_cases} testId="intel-open-cases" icon={Icons.Warning} />
      </ResponsiveGrid>

      <ResponsiveGrid columns="two" className="mb-4">
        <HeatmapGrid title="Month Risk Heatmap" cells={heatmaps?.months} testId="intel-heatmap-months" />
        <HeatmapGrid title="Category Risk Heatmap" cells={heatmaps?.categories} testId="intel-heatmap-categories" />
      </ResponsiveGrid>

      {patterns?.length > 0 && (
        <div className="mb-4" data-testid="intel-patterns">
          <h4 className={cn(theme.text.label, 'font-semibold mb-2')}>Detected Patterns</h4>
          <ul className="space-y-1.5 text-xs">
            {patterns.slice(0, 5).map((p) => (
              <li key={p.pattern_type + p.description} className={cn(theme.alert.warning, 'px-3 py-2 flex justify-between gap-2 rounded-lg')}>
                <span>{p.description}</span>
                <PriorityBadge priority={p.severity} label={p.severity} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {insights?.top_risks?.length > 0 && (
        <div data-testid="intel-top-risks">
          <h4 className={cn(theme.text.label, 'font-semibold mb-2')}>Top Risks</h4>
          <ul className={cn('text-xs list-disc list-inside space-y-1', theme.text.muted)}>
            {insights.top_risks.slice(0, 5).map((r) => <li key={r}>{r}</li>)}
          </ul>
        </div>
      )}
    </ContentCard>
  );
}
