import React from 'react';
import { cn } from '../../lib/utils';
import theme from '../../theme/theme';
import { forms } from '../../theme/forms';

const Input = React.forwardRef(({ className, error, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(forms.input, error && forms.inputError, className)}
    {...props}
  />
));
Input.displayName = 'Input';

const Textarea = React.forwardRef(({ className, error, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(forms.input, 'min-h-[80px] resize-y', error && forms.inputError, className)}
    {...props}
  />
));
Textarea.displayName = 'Textarea';

const Label = React.forwardRef(({ className, ...props }, ref) => (
  <label ref={ref} className={cn(forms.label, className)} {...props} />
));
Label.displayName = 'Label';

export { Input, Textarea, Label };
