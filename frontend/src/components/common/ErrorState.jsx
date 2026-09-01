import React from 'react';
import { AlertCircle } from '../../theme/icons';
import { iconSize } from '../../theme/icons';
import { cn } from '../../lib/utils';

export default function ErrorState({ title = 'Something went wrong', message, className, testId = 'error-state' }) {
  return (
    <div
      className={cn('rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger', className)}
      data-testid={testId}
      role="alert"
    >
      <div className="flex items-start gap-2">
        <AlertCircle className={cn(iconSize.sm, 'mt-0.5 shrink-0')} />
        <div>
          <p className="font-medium">{title}</p>
          {message && <p className="mt-1 opacity-90">{message}</p>}
        </div>
      </div>
    </div>
  );
}
