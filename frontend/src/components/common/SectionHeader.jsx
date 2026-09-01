import React from 'react';
import { cn } from '../../lib/utils';

export default function SectionHeader({ title, description, actions, className, testId }) {
  return (
    <div className={cn('flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between mb-4', className)} data-testid={testId}>
      <div>
        {title && <h2 className="text-lg font-semibold">{title}</h2>}
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      {actions}
    </div>
  );
}
