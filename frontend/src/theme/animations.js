/** Animation presets — single source for motion across GAIS. */
export const fadeIn = 'animate-fade-in';
export const spin = 'animate-spin';
export const pulse = 'animate-pulse';

export const slideIn = 'animate-in slide-in-from-bottom-2 duration-200';
export const slideOut = 'animate-out slide-out-to-bottom-2 duration-200';

export const modalEnter = 'animate-in fade-in zoom-in-95 duration-200';
export const modalExit = 'animate-out fade-out zoom-out-95 duration-200';

export const tooltipEnter = 'animate-in fade-in duration-150';
export const drawerEnter = 'animate-in slide-in-from-right duration-300';
export const drawerExit = 'animate-out slide-out-to-right duration-300';

export const toastEnter = 'animate-in slide-in-from-top-2 fade-in duration-300';
export const loading = 'animate-pulse opacity-70 pointer-events-none';
export const spinner = spin;

export const transition = {
  colors: 'transition-colors duration-200',
  all: 'transition-all duration-200',
  theme: 'background-color 0.3s ease, color 0.3s ease',
};

export const animations = {
  fadeIn,
  spin,
  pulse,
  slideIn,
  slideOut,
  modal: { enter: modalEnter, exit: modalExit },
  tooltip: tooltipEnter,
  drawer: { enter: drawerEnter, exit: drawerExit },
  toast: toastEnter,
  loading,
  spinner,
  transition,
};

export default animations;
