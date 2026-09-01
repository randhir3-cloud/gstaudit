import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from '../ui/tooltip';

/** Accessible tooltip wrapper — replaces CSS-only StatusTooltip */
export default function StatusTooltip({ children, title, details = [] }) {
  const lines = details.filter(Boolean);
  if (!lines.length) return children;

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex">{children}</span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[220px]">
          {title && <p className="font-semibold mb-1">{title}</p>}
          {lines.map((line) => (
            <p key={line} className="text-muted-foreground">{line}</p>
          ))}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
