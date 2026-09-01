/** Workflow / dataset status tokens */
export const statusColors = {
  draft: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
  pending: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
  uploaded: 'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
  merged: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
  complete: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
  in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  running: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-300',
  error: 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-300',
  not_started: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400',
  open: 'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
  closed: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400',
  resolved: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
};

export function statusClassName(status) {
  const key = String(status || 'pending').toLowerCase().replace(/\s+/g, '_');
  return statusColors[key] || statusColors.pending;
}
