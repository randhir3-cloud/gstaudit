import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';

export default function Toolbar({ children, className, testId }) {
  return (
    <div className={cn(theme.layout.toolbarShell, className)} data-testid={testId}>
      {children}
    </div>
  );
}
