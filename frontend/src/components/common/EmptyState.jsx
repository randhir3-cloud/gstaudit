import React from 'react';
import { cn } from '../../lib/utils';

export default function EmptyState({ title = 'No data', description, action, className, testId = 'empty-state' }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)} data-testid={testId}>
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && <p className="text-xs text-muted-foreground mt-1 max-w-sm">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
