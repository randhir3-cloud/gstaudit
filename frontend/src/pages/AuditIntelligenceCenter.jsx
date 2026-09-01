import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/layout/PageLayout';
import PageHeader from '../components/common/PageHeader';
import ContentCard from '../components/cards/ContentCard';
import RiskCard from '../components/cards/RiskCard';
import ResponsiveGrid from '../components/layout/ResponsiveGrid';
import EmptyState from '../components/common/EmptyState';
import LoadingState from '../components/common/LoadingState';
import PriorityBadge from '../components/badges/PriorityBadge';
import { Button } from '../components/ui/button';
import { useAuditSession } from '../context/AuditSessionContext';
import { Icons } from '../icons';
import theme from '../theme/theme';
import { cn } from '../lib/utils';
import {
  fetchMsae,
  fetchMsaeCaseDetail,
  orchestrateMsae,
} from '../api/msae';

function HeatmapGrid({ title, cells, testId }) {
  if (!cells?.length) return null;
  const maxRisk = Math.max(...cells.map((c) => c.risk_score || 0), 1);
  return (
    <div data-testid={testId}>
      <h4 className={cn(theme.text.label, 'font-semibold mb-2')}>{title}</h4>
      <div className="flex flex-wrap gap-1.5">
        {cells.slice(0, 10).map((cell) => {
          const intensity = Math.round((cell.risk_score / maxRisk) * 100);
          return (
            <div
              key={cell.label}
              className="rounded-lg px-2 py-1 text-[10px] border border-border"
              style={{ backgroundColor: `rgba(239, 68, 68, ${intensity / 200})` }}
              title={`${cell.label}: ${cell.count} issues`}
            >
              <span className="font-medium">{cell.label.slice(0, 14)}</span>
              <span className={cn('ml-1 tabular-nums', theme.text.muted)}>{cell.count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TrendChart({ trend, testId }) {
  if (!trend?.length) return null;
  const max = Math.max(...trend.map((t) => t.count), 1);
  return (
    <div data-testid={testId}>
      <h4 className={cn(theme.text.label, 'font-semibold mb-2')}>Discrepancy Trend</h4>
      <div className="flex items-end gap-1 h-24">
        {trend.slice(0, 12).map((item) => (
          <div key={item.period} className="flex-1 flex flex-col items-center gap-1" title={`${item.period}: ${item.count}`}>
            <div
              className="w-full bg-primary/70 rounded-t"
              style={{ height: `${Math.max(8, (item.count / max) * 100)}%` }}
            />
            <span className="text-[9px] text-muted-foreground truncate w-full text-center">{item.period.slice(0, 6)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MasterCaseRow({ caseItem, sessionId, expanded, onToggle }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!expanded || detail) return;
    setLoading(true);
    fetchMsaeCaseDetail(sessionId, caseItem.master_case_id)
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [expanded, detail, sessionId, caseItem.master_case_id]);

  return (
    <>
      <tr
        className="border-b border-border hover:bg-muted/30 cursor-pointer"
        onClick={onToggle}
        data-testid={`msae-case-row-${caseItem.master_case_id}`}
      >
        <td className="px-3 py-2 text-xs font-medium">{caseItem.case_number}</td>
        <td className="px-3 py-2 text-xs">{caseItem.invoice_number || caseItem.normalized_invoice}</td>
        <td className="px-3 py-2 text-xs tabular-nums">{caseItem.source_count}</td>
        <td className="px-3 py-2 text-xs tabular-nums">{caseItem.risk_score}</td>
        <td className="px-3 py-2"><PriorityBadge priority={caseItem.priority} label={caseItem.priority} /></td>
        <td className="px-3 py-2 text-xs text-muted-foreground">{caseItem.comparison_ids?.join(', ')}</td>
      </tr>
      {expanded && (
        <tr data-testid={`msae-case-detail-${caseItem.master_case_id}`}>
          <td colSpan={6} className="px-4 py-3 bg-muted/20">
            {loading && <LoadingState label="Loading findings…" />}
            {!loading && (
              <div className="space-y-2">
                {caseItem.patterns?.length > 0 && (
                  <ul className="text-xs text-amber-700 dark:text-amber-300 list-disc list-inside">
                    {caseItem.patterns.map((p) => <li key={p}>{p}</li>)}
                  </ul>
                )}
                <div className="text-xs font-semibold mb-1">Plugin Findings</div>
                <ul className="space-y-1.5">
                  {(detail?.child_findings || caseItem.child_findings || []).map((f) => (
                    <li
                      key={f.finding_id}
                      className="flex justify-between gap-2 text-xs border border-border rounded px-2 py-1.5"
                      data-testid={`msae-finding-${f.finding_id}`}
                    >
                      <span>{f.comparison_label}: {f.description}</span>
                      <PriorityBadge priority={f.risk_score >= 70 ? 'High' : 'Medium'} label={f.result_type} />
                    </li>
                  ))}
                </ul>
                <Link to="/investigation" className="text-xs text-primary font-medium">Open Investigation Workbench →</Link>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

export default function AuditIntelligenceCenter() {
  const { session } = useAuditSession();
  const sessionId = session?.session_id;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError('');
    try {
      const result = await fetchMsae(sessionId);
      setData(result);
    } catch (err) {
      setError(err.message || 'Failed to load audit intelligence');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleRefresh = async () => {
    if (!sessionId) return;
    setRefreshing(true);
    try {
      await orchestrateMsae(sessionId);
      await load();
    } finally {
      setRefreshing(false);
    }
  };

  const summary = data?.summary;
  const scores = summary?.scores;

  return (
    <DashboardLayout testId="audit-intelligence-center">
      <PageHeader
        title="Audit Intelligence Center"
        description="Multi-Source Audit Engine — consolidated findings across all comparison plugins"
        actions={(
          <Button
            size="sm"
            variant="outline"
            onClick={handleRefresh}
            disabled={!sessionId || refreshing}
            data-testid="msae-refresh"
          >
            {refreshing ? 'Orchestrating…' : 'Re-orchestrate'}
          </Button>
        )}
      />

      {!sessionId && (
        <EmptyState
          title="No audit session loaded"
          description="Load a session and run comparisons to generate consolidated audit intelligence."
        />
      )}

      {sessionId && loading && <LoadingState label="Loading consolidated audit intelligence…" />}

      {sessionId && error && (
        <ContentCard testId="msae-error">
          <p className="text-sm text-destructive">{error}</p>
        </ContentCard>
      )}

      {sessionId && !loading && data && (
        <div className="space-y-5">
          <ResponsiveGrid columns="six" testId="msae-score-cards">
            <RiskCard label="Master Cases" value={summary.master_case_count} testId="msae-master-cases-kpi" icon={Icons.Investigate} />
            <RiskCard label="Cross-Plugin" value={summary.cross_plugin_case_count} testId="msae-cross-plugin" icon={Icons.Compare} highlight={summary.cross_plugin_case_count > 0} />
            <RiskCard label="High Risk" value={summary.high_risk_cases} testId="msae-high-risk" icon={Icons.Warning} highlight={summary.high_risk_cases > 0} />
            <RiskCard label="Dealer Risk" value={`${scores?.dealer_risk_score ?? 0}/100`} testId="msae-dealer-risk" icon={Icons.Building} />
            <RiskCard label="Officer Priority" value={`${scores?.officer_priority_score ?? 0}/100`} testId="msae-officer-priority" icon={Icons.Shield} />
            <RiskCard label="Audit Confidence" value={`${Math.round((scores?.audit_confidence ?? 0) * 100)}%`} testId="msae-confidence" icon={Icons.Sparkles} />
          </ResponsiveGrid>

          {summary.top_risks?.length > 0 && (
            <ContentCard testId="msae-top-risks" title="Top Risks" description="Highest-priority consolidated audit signals">
              <ul className="text-sm space-y-1.5 list-disc list-inside text-muted-foreground">
                {summary.top_risks.map((r) => <li key={r}>{r}</li>)}
              </ul>
            </ContentCard>
          )}

          <ResponsiveGrid columns="two">
            <ContentCard testId="msae-heatmaps" title="Risk Heatmaps">
              <HeatmapGrid title="Month Risk" cells={data.heatmaps?.months} testId="msae-heatmap-months" />
              <HeatmapGrid title="Category Risk" cells={data.heatmaps?.categories} testId="msae-heatmap-categories" />
            </ContentCard>
            <ContentCard testId="msae-trend" title="Trend Analysis">
              <TrendChart trend={data.trend} testId="msae-trend-chart" />
            </ContentCard>
          </ResponsiveGrid>

          {data.patterns?.length > 0 && (
            <ContentCard testId="msae-patterns" title="Cross-Source Patterns">
              <ul className="space-y-1.5 text-xs">
                {data.patterns.slice(0, 8).map((p) => (
                  <li key={p.pattern_type + p.description} className={cn(theme.alert.warning, 'px-3 py-2 flex justify-between gap-2 rounded-lg')}>
                    <span>{p.description}</span>
                    <PriorityBadge priority={p.severity} label={p.severity} />
                  </li>
                ))}
              </ul>
            </ContentCard>
          )}

          <ContentCard
            testId="msae-master-cases-panel"
            title="Master Investigation Cases"
            description="One consolidated case per invoice — expand to view plugin findings"
            actions={<Link to="/investigation" className="text-xs text-primary font-medium">Investigation Workbench →</Link>}
          >
            {data.master_cases?.length === 0 ? (
              <EmptyState title="No discrepancies" description="Run comparison plugins to populate master cases." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-border text-xs text-muted-foreground">
                      <th className="px-3 py-2">Case</th>
                      <th className="px-3 py-2">Invoice</th>
                      <th className="px-3 py-2">Sources</th>
                      <th className="px-3 py-2">Risk</th>
                      <th className="px-3 py-2">Priority</th>
                      <th className="px-3 py-2">Plugins</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.master_cases.slice(0, 25).map((c) => (
                      <MasterCaseRow
                        key={c.master_case_id}
                        caseItem={c}
                        sessionId={sessionId}
                        expanded={expandedId === c.master_case_id}
                        onToggle={() => setExpandedId(expandedId === c.master_case_id ? null : c.master_case_id)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </ContentCard>

          {data.timeline?.length > 0 && (
            <ContentCard testId="msae-timeline" title="Audit Timeline">
              <ol className="space-y-2 text-xs border-l-2 border-border ml-2 pl-4">
                {data.timeline.slice(-12).map((evt, i) => (
                  <li key={`${evt.stage}-${i}`} data-testid={`msae-timeline-${evt.stage}`}>
                    <span className="font-medium capitalize">{evt.stage.replace('_', ' ')}</span>
                    <span className="text-muted-foreground"> — {evt.title}</span>
                    {evt.description && <div className="text-muted-foreground">{evt.description}</div>}
                  </li>
                ))}
              </ol>
            </ContentCard>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}
