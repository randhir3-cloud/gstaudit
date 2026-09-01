import React from 'react';
import { cn } from '../../lib/utils';

export default function PageHeader({ title, description, actions, className, testId }) {
  return (
    <header className={cn('flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between mb-6', className)} data-testid={testId}>
      <div>
        {title && <h1 className="text-2xl font-bold tracking-tight">{title}</h1>}
        {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
