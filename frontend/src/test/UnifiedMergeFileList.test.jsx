import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import UnifiedMergeFileList from '../components/merge/UnifiedMergeFileList';

describe('UnifiedMergeFileList Component', () => {
  const sampleEwayFiles = [
    {
      id: 'f1',
      name: 'Inward April 1.xls',
      size: 4096,
      period: 'Apr-2023',
      classification: {
        detected_type: 'inward',
        confidence: 100,
        dealer_gstin: '03AAACC1205A1ZX',
        month: 'Apr 2023',
        financial_year: '2023-24',
        status: 'valid',
      },
    },
    {
      id: 'f2',
      name: 'Inward May 1.xls',
      size: 8192,
      period: 'May-2023',
      classification: {
        detected_type: 'inward',
        confidence: 100,
        dealer_gstin: '03AAACC1205A1ZX',
        month: 'May 2023',
        financial_year: '2023-24',
        status: 'valid',
      },
    },
    {
      id: 'f3',
      name: 'Outward June 1.xls',
      size: 6144,
      period: 'Jun-2023',
      classification: {
        detected_type: 'outward',
        confidence: 95,
        dealer_gstin: '03AAACC1205A1ZX',
        month: 'Jun 2023',
        financial_year: '2023-24',
        status: 'wrong_section',
      },
    },
  ];

  it('Renders exactly 3 rows for 3 uploaded files (No duplication)', () => {
    render(
      <UnifiedMergeFileList
        files={sampleEwayFiles}
        mode="eway"
        onMoveUp={vi.fn()}
        onMoveDown={vi.fn()}
        onRemove={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    // Header count badge should display 3
    expect(screen.getByText('3')).toBeDefined();

    // Verify all 3 filenames are present exactly once
    expect(screen.getByText('Inward April 1.xls')).toBeDefined();
    expect(screen.getByText('Inward May 1.xls')).toBeDefined();
    expect(screen.getByText('Outward June 1.xls')).toBeDefined();

    // Verify metadata & validation badges are present on each unified row
    expect(screen.getAllByText('INWARD').length).toBe(2);
    expect(screen.getByText('OUTWARD')).toBeDefined();
    expect(screen.getAllByText('100%').length).toBe(2);
    expect(screen.getByText('95%')).toBeDefined();
    expect(screen.getAllByText('03AAACC1205A1ZX').length).toBe(3);
    expect(screen.getAllByText('valid').length).toBe(2);
    expect(screen.getByText('wrong section')).toBeDefined();
  });

  it('Supports Move Up, Move Down, and Remove actions from the unified row', () => {
    const handleMoveUp = vi.fn();
    const handleMoveDown = vi.fn();
    const handleRemove = vi.fn();

    render(
      <UnifiedMergeFileList
        files={sampleEwayFiles}
        mode="eway"
        onMoveUp={handleMoveUp}
        onMoveDown={handleMoveDown}
        onRemove={handleRemove}
        onClearAll={vi.fn()}
      />
    );

    // Trigger action buttons for second file
    const moveUpBtn = screen.getByRole('button', { name: /Move Inward May 1.xls up/i });
    fireEvent.click(moveUpBtn);
    expect(handleMoveUp).toHaveBeenCalledWith(1);

    const moveDownBtn = screen.getByRole('button', { name: /Move Inward May 1.xls down/i });
    fireEvent.click(moveDownBtn);
    expect(handleMoveDown).toHaveBeenCalledWith(1);

    const removeBtn = screen.getByRole('button', { name: /Remove Inward May 1.xls/i });
    fireEvent.click(removeBtn);
    expect(handleRemove).toHaveBeenCalledWith('f2');
  });

  it('Triggers Clear All correctly', () => {
    const handleClearAll = vi.fn();
    render(
      <UnifiedMergeFileList
        files={sampleEwayFiles}
        mode="eway"
        onMoveUp={vi.fn()}
        onMoveDown={vi.fn()}
        onRemove={vi.fn()}
        onClearAll={handleClearAll}
      />
    );

    const clearAllBtn = screen.getByRole('button', { name: /Clear All/i });
    fireEvent.click(clearAllBtn);
    expect(handleClearAll).toHaveBeenCalledTimes(1);
  });
});
