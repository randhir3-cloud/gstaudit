import React from 'react';
import StatusBadge from '../common/StatusBadge';

export default function ComparisonBadge({ status, label }) {
  return <StatusBadge status={status} label={label ?? status} />;
}
