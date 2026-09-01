/** Form field tokens — use with shadcn Form/Input wrappers. */
export const formLabel = 'text-sm font-medium text-foreground';
export const formDescription = 'text-xs text-muted-foreground';
export const formError = 'text-xs text-danger mt-1';
export const formField = 'space-y-1.5';
export const formGroup = 'space-y-4';

export const inputBase =
  'flex w-full rounded-lg border border-border bg-background px-3 py-2 text-sm '
  + 'placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 '
  + 'focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50';

export const inputError = 'border-danger focus-visible:ring-danger';

export const forms = {
  label: formLabel,
  description: formDescription,
  error: formError,
  field: formField,
  group: formGroup,
  input: inputBase,
  inputError,
};

export default forms;
