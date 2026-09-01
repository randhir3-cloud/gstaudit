import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';
import SectionHeader from '../common/SectionHeader';

export default function ContentCard({
  title,
  description,
  actions,
  children,
  className,
  testId,
  headerClassName,
  bodyClassName,
  noPadding,
}) {
  return (
    <div className={cn(theme.card.shell, className)} data-testid={testId}>
      {title && (
        <SectionHeader
          title={title}
          description={description}
          actions={actions}
          className={cn('mb-0', headerClassName)}
        />
      )}
      <div className={cn(title && 'mt-4', !noPadding && bodyClassName)}>
        {children}
      </div>
    </div>
  );
}

export function ContentCardHeader({ title, children, testId }) {
  return (
    <div className={cn(theme.card.header)} data-testid={testId}>
      {title ? <h3 className={theme.text.sectionTitle}>{title}</h3> : children}
    </div>
  );
}
