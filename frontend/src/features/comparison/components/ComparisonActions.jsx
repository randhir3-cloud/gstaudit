import React from 'react';
import { Button } from '../../../components/ui/button';
import { Icons } from '../../../icons';

export default function ComparisonActions({ loading, onRun }) {
  return (
    <Button
      onClick={onRun}
      disabled={loading}
      data-testid="run-comparison-btn"
    >
      {loading ? (
        <Icons.Loading className={`${Icons.size.sm} animate-spin`} />
      ) : (
        <Icons.Play className={Icons.size.sm} />
      )}
      Run Comparison
    </Button>
  );
}
