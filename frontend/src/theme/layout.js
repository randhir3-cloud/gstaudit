import { pagePadding, sectionGap } from './spacing';

/** Page and grid layout tokens. */
export const pageMaxWidth = 'max-w-7xl';
export const pageShell = `mx-auto w-full ${pageMaxWidth} ${pagePadding}`;

export const toolbarHeight = 'h-12';
export const toolbarShell =
  'flex flex-wrap items-center justify-between gap-3 mb-4 min-h-[3rem]';

export const gridGap = sectionGap;
export const dashboardGrid = 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4';
export const statsGrid = 'grid grid-cols-2 md:grid-cols-4 gap-4';
export const responsiveGrid = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4';
export const twoColumnLayout = 'grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6';
export const threePanelLayout = 'grid grid-cols-1 lg:grid-cols-[240px_1fr_320px] gap-4';

export const layout = {
  pageMaxWidth,
  pageShell,
  toolbarHeight,
  toolbarShell,
  gridGap,
  dashboardGrid,
  statsGrid,
  responsiveGrid,
  twoColumnLayout,
  threePanelLayout,
};

export default layout;
