import { useState, useCallback } from 'react';

export function usePagination(items, pageSize = 25) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = items.slice(safePage * pageSize, (safePage + 1) * pageSize);

  return {
    page: safePage,
    setPage,
    pageCount,
    pageRows,
    pageSize,
  };
}
