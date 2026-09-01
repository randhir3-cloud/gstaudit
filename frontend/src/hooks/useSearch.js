import { useState, useCallback, useMemo } from 'react';

export function useSearch(initial = '') {
  const [search, setSearch] = useState(initial);

  const filterRows = useCallback((rows, keys) => {
    if (!search) return rows;
    const q = search.toLowerCase();
    return rows.filter((row) =>
      keys.some((key) => String(row[key] ?? '').toLowerCase().includes(q)),
    );
  }, [search]);

  return { search, setSearch, filterRows };
}

export function useFiltering(initialFilters = {}) {
  const [filters, setFilters] = useState(initialFilters);

  const setFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const clearFilters = useCallback(() => setFilters(initialFilters), [initialFilters]);

  const applyFilters = useCallback((rows, predicate) => {
    if (!predicate) return rows;
    return rows.filter(predicate);
  }, []);

  return { filters, setFilter, clearFilters, applyFilters };
}
