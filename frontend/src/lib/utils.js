import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge Tailwind classes with conflict resolution (shadcn pattern). */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
