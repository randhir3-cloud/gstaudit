import React from 'react';
import { Button } from '../../../components/ui/button';

export default function CaseActions({ selectedCount, onBulkVerify, onBulkPending }) {
  if (!selectedCount) return null;

  return (
    <div className="flex gap-2 mb-3" data-testid="bulk-actions" role="group" aria-label="Bulk case actions">
      <Button type="button" variant="secondary" size="sm" onClick={onBulkVerify} data-testid="bulk-verify">
        Mark Verified
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={onBulkPending} data-testid="bulk-pending">
        Mark Pending
      </Button>
    </div>
  );
}
