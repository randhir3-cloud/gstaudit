/**
 * GAIS frontend plugin registry — loads manifests from platform API.
 */
import { fetchPluginCatalog } from '../api/plugins';

let catalog = null;

export async function loadPluginCatalog() {
  if (catalog) return catalog;
  catalog = await fetchPluginCatalog();
  return catalog;
}

export function getPluginCatalog() {
  return catalog;
}

export function getRegisteredDatasets() {
  return catalog?.datasets ?? {};
}

export function getRegisteredComparisonPairs() {
  return catalog?.comparison_pairs ?? [];
}

export function getPluginNavigation() {
  return catalog?.navigation ?? [];
}

export async function ensurePluginsLoaded() {
  return loadPluginCatalog();
}
