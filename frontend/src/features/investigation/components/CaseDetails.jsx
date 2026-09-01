import React from 'react';
import PriorityBadge from '../../../components/badges/PriorityBadge';
import { Button } from '../../../components/ui/button';
import theme from '../../../theme/theme';
import { cn } from '../../../lib/utils';

function DetailItem({ label, value, testId }) {
  return (
    <div>
      <dt className={theme.text.label}>{label}</dt>
      <dd className={cn(theme.text.body, 'font-medium')} data-testid={testId}>{value ?? '—'}</dd>
    </div>
  );
}

export default function CaseSummary({ caseData }) {
  if (!caseData) return null;

  return (
    <div>
      <p className={theme.text.label}>{caseData.case_number}</p>
      <h3 className={theme.text.subheading}>{caseData.invoice_number}</h3>
      <div className="flex flex-wrap gap-2 mt-2">
        <PriorityBadge
          priority={caseData.priority}
          score={caseData.priority_score || caseData.risk_score}
          testId="case-priority-badge"
        />
      </div>
      <dl className={cn('grid grid-cols-2 gap-2 mt-4', theme.text.label)}>
        <DetailItem label="Supplier GSTIN" value={caseData.supplier_gstin} />
        <DetailItem label="Recipient GSTIN" value={caseData.recipient_gstin} />
        <DetailItem label="Invoice Date" value={caseData.invoice_date} />
        <DetailItem label="Invoice Value" value={caseData.invoice_value?.toLocaleString?.('en-IN')} />
        <DetailItem label="Taxable Value" value={caseData.taxable_value?.toLocaleString?.('en-IN')} />
        <DetailItem
          label="Comparison"
          value={caseData.comparison_result}
        />
        <DetailItem label="Risk Score" value={caseData.risk_score} testId="case-risk-score" />
      </dl>
    </div>
  );
}

function InfoBlock({ title, items, variant = 'info', testId }) {
  if (!items?.length) return null;
  const variantClass = {
    danger: theme.alert.error,
    warning: theme.alert.warning,
    info: theme.alert.info,
    success: 'rounded-xl border border-success/30 bg-success/10 p-3 text-xs text-success',
    muted: cn(theme.card.shell, 'p-3 text-xs'),
  }[variant];

  return (
    <div className={variantClass} data-testid={testId}>
      <p className="font-semibold">{title}</p>
      <ul className="mt-1 list-disc list-inside space-y-0.5">{items.map((item) => <li key={item}>{item}</li>)}</ul>
    </div>
  );
}

export function CaseDetailsContent({ caseData, onSave, saving }) {
  const [remarks, setRemarks] = React.useState('');
  const [status, setStatus] = React.useState('Pending');
  const [attachments, setAttachments] = React.useState({
    notes: '',
    reference_number: '',
    document_reference: '',
    book_page: '',
    supporting_evidence: '',
  });

  React.useEffect(() => {
    if (!caseData) return;
    setRemarks(caseData.officer_remarks || '');
    setStatus(caseData.status || 'Pending');
    setAttachments(caseData.attachments || {
      notes: '',
      reference_number: '',
      document_reference: '',
      book_page: '',
      supporting_evidence: '',
    });
  }, [caseData?.case_id]);

  if (!caseData) {
    return (
      <aside
        className={cn(theme.card.dashed, 'text-sm max-h-[85vh]')}
        data-testid="investigation-details-empty"
      >
        Select a discrepancy to investigate.
      </aside>
    );
  }

  return (
    <aside
      className={cn(theme.card.shell, 'space-y-4 max-h-[85vh] overflow-y-auto')}
      data-testid="investigation-details"
    >
      <CaseSummary caseData={caseData} />

      {caseData.priority_reason && (
        <InfoBlock
          title="Priority Reason"
          items={[caseData.priority_reason]}
          variant="danger"
          testId="case-priority-reason"
        />
      )}

      <InfoBlock title="Detected Patterns" items={caseData.patterns} variant="info" testId="case-patterns" />
      <InfoBlock title="Possible Causes" items={caseData.possible_causes} variant="warning" testId="case-possible-causes" />
      <InfoBlock title="Recommended Documents" items={caseData.recommended_documents} variant="success" testId="case-recommended-documents" />
      <InfoBlock title="Suggested Verification" items={caseData.suggested_verifications} variant="info" testId="case-suggested-verification" />
      <InfoBlock title="Applicable Provisions" items={caseData.gst_provisions} variant="muted" testId="case-gst-provisions" />

      {caseData.related_case_ids?.length > 0 && (
        <div className={theme.text.label} data-testid="case-related">
          <p className="font-semibold">Related Cases</p>
          <p className={cn(theme.text.mono, 'mt-1 text-muted-foreground')}>
            {caseData.related_case_ids.join(', ')}
          </p>
        </div>
      )}

      <div className={theme.forms.field}>
        <label className={theme.forms.label} htmlFor="case-status-select">Status</label>
        <select
          id="case-status-select"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className={theme.forms.input}
          data-testid="case-status-select"
        >
          {['Pending', 'Verified', 'Accepted', 'Rejected', 'Needs Clarification', 'Additional Documents Required'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className={theme.forms.field}>
        <label className={theme.forms.label} htmlFor="case-remarks-input">Officer Remarks</label>
        <textarea
          id="case-remarks-input"
          value={remarks}
          onChange={(e) => setRemarks(e.target.value)}
          rows={3}
          className={theme.forms.input}
          data-testid="case-remarks-input"
        />
      </div>

      <fieldset className={cn(theme.forms.field, theme.card.shell, 'p-3 border-border')}>
        <legend className={cn(theme.forms.label, 'px-1 font-semibold')}>Attachments (reference only)</legend>
        {['notes', 'reference_number', 'document_reference', 'book_page', 'supporting_evidence'].map((field) => (
          <input
            key={field}
            placeholder={field.replace(/_/g, ' ')}
            value={attachments[field] || ''}
            onChange={(e) => setAttachments({ ...attachments, [field]: e.target.value })}
            className={cn(theme.forms.input, 'mt-2')}
            data-testid={`attachment-${field}`}
          />
        ))}
      </fieldset>

      <Button
        type="button"
        disabled={saving}
        onClick={() => onSave({ status, officer_remarks: remarks, attachments })}
        className="w-full"
        data-testid="save-case-btn"
      >
        {saving ? 'Saving…' : 'Save Investigation'}
      </Button>
    </aside>
  );
}
