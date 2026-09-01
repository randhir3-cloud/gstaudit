import { useState, useCallback } from 'react';

export function useSorting(initialKey = '', initialDir = 'desc') {
  const [sortKey, setSortKey] = useState(initialKey);
  const [sortDir, setSortDir] = useState(initialDir);

  const toggleSort = useCallback((key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  }, [sortKey]);

  const sortRows = useCallback((rows, key, accessor) => {
    const k = key || sortKey;
    const get = accessor || ((row) => row[k] ?? '');
    return [...rows].sort((a, b) => {
      const av = get(a);
      const bv = get(b);
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [sortKey, sortDir]);

  return { sortKey, sortDir, setSortKey, setSortDir, toggleSort, sortRows };
}
