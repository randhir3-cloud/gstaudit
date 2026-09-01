import React from 'react';
import AuditStatusBadge from '../common/StatusBadge';

export default function AuditBadge({ status, label }) {
  const text = label ?? (status ? `Audit: ${String(status).replace('_', ' ')}` : 'Audit');
  return <AuditStatusBadge status={status} label={text} />;
}
