import React from 'react';
import { Loader2 } from '../../theme/icons';
import { iconSize } from '../../theme/icons';
import { cn } from '../../lib/utils';

export default function LoadingState({ message = 'Loading…', className, testId = 'loading-state' }) {
  return (
    <div className={cn('flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground', className)} data-testid={testId}>
      <Loader2 className={cn(iconSize.sm, 'animate-spin text-primary')} />
      <span>{message}</span>
    </div>
  );
}
