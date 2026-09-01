import React from 'react';
import ContentCard from '../../../components/cards/ContentCard';
import theme from '../../../theme/theme';
import { cn } from '../../../lib/utils';
import { INVESTIGATION_CATEGORIES } from '../constants';

export default function CaseSidebar({ active, onSelect, categories = {}, summary }) {
  return (
    <ContentCard testId="investigation-categories" noPadding>
      <h3 className={cn(theme.text.sectionTitle, 'text-sm mb-3')}>Discrepancy Categories</h3>
      <ul className="space-y-1" role="list">
        {INVESTIGATION_CATEGORIES.map(({ key, label }) => {
          const count = key === 'ALL' ? summary?.total : categories[label] ?? 0;
          const isActive = active === key;
          return (
            <li key={key}>
              <button
                type="button"
                onClick={() => onSelect(key)}
                className={cn(
                  'w-full text-left text-xs px-3 py-2 rounded-lg flex justify-between transition-colors',
                  theme.sidebar.item,
                  isActive && theme.sidebar.itemActive,
                )}
                data-testid={`category-${key}`}
                aria-current={isActive ? 'true' : undefined}
              >
                <span>{label}</span>
                <span className="tabular-nums font-semibold">{count ?? 0}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </ContentCard>
  );
}
