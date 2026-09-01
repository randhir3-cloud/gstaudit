import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';

export default function SectionContainer({ children, className, testId, title, description }) {
  return (
    <section className={cn(className)} data-testid={testId}>
      {title && (
        <h3 className={cn(theme.text.sectionTitle, 'mb-4')}>{title}</h3>
      )}
      {description && <p className={cn(theme.text.muted, 'mb-4')}>{description}</p>}
      {children}
    </section>
  );
}
