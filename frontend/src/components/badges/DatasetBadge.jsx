import React from 'react';
import StatusBadge from '../common/StatusBadge';

const DATASET_STATUS_MAP = {
  Empty: 'empty',
  empty: 'empty',
  Uploaded: 'uploaded',
  uploaded: 'uploaded',
  Ready: 'merged',
  merged: 'merged',
};

export default function DatasetBadge({ status, label }) {
  const mapped = DATASET_STATUS_MAP[status] || status || 'empty';
  return <StatusBadge status={mapped} label={label ?? status} />;
}
