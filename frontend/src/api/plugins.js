import { API_BASE, apiFetch } from './client';

export async function fetchPluginCatalog() {
  return apiFetch(`${API_BASE}/api/plugins`);
}
