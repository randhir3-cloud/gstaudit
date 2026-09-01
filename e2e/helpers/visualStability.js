import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const evidenceDir = path.join(__dirname, '..', '..', 'docs', 'evidence', '2026-07-09');

/**
 * Wait until the UI is visually stable for evidence capture.
 * - network idle
 * - no loading spinners
 * - no modal backdrop (unless allowModal)
 * - body/html opacity at 1
 * - CSS transitions settled
 */
export async function waitForVisualStability(page, { allowModal = false } = {}) {
  await page.waitForLoadState('networkidle');

  // Lucide Loader2 and other spinners use animate-spin
  await page.locator('.animate-spin').first().waitFor({ state: 'hidden', timeout: 10_000 }).catch(() => {});

  await page.waitForFunction(
    (allow) => {
      const htmlOpacity = parseFloat(getComputedStyle(document.documentElement).opacity || '1');
      const bodyOpacity = parseFloat(getComputedStyle(document.body).opacity || '1');
      if (htmlOpacity < 0.99 || bodyOpacity < 0.99) return false;

      for (const el of document.querySelectorAll('*')) {
        const style = getComputedStyle(el);
        const cls = el.className?.toString?.() || '';
        const testId = el.dataset?.testid || '';
        const isFixed = style.position === 'fixed';
        const isBackdrop = testId === 'modal-backdrop' || /bg-black\/\d+/.test(cls);
        const isDialogOverlay = isFixed && el.getAttribute('role') === 'dialog' && isBackdrop;
        if (!allow && (isBackdrop || isDialogOverlay)) return false;
      }

      // Vite error overlay should never appear in evidence
      if (document.querySelector('vite-error-overlay')) return false;

      return true;
    },
    allowModal,
    { timeout: 10_000 },
  );

  // Theme class is applied in useEffect — wait for dark/light class to match stored preference
  await page.waitForFunction(() => {
    const theme = localStorage.getItem('theme') || 'dark';
    const isDark = document.documentElement.classList.contains('dark');
    return theme === 'dark' ? isDark : !isDark;
  }, { timeout: 5000 });

  // Theme/body transitions use 300ms (index.css)
  await page.waitForTimeout(350);
}

/**
 * Capture evidence screenshot matching the user viewport (not fullPage).
 * fullPage stitching duplicates sticky backdrop-blur headers, causing a grey dim overlay.
 */
export async function saveEvidence(page, name, { allowModal = false, fullPage = false, dir = evidenceDir } = {}) {
  await waitForVisualStability(page, { allowModal });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(100);
  fs.mkdirSync(dir, { recursive: true });
  await page.screenshot({
    path: path.join(dir, `${name}.png`),
    fullPage,
  });
}
