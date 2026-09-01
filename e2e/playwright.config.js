import { defineConfig, devices } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const evidenceDir = path.join(__dirname, '..', 'docs', 'evidence');

export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.js',
  globalSetup: './global-setup.js',
  fullyParallel: false,
  timeout: 60_000,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: path.join(evidenceDir, 'playwright-report'), open: 'never' }]],
  outputDir: path.join(evidenceDir, 'playwright-output'),
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    screenshot: 'on',
    video: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: '**/dashboard-viewport.spec.js',
    },
    {
      name: 'viewport',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/dashboard-viewport.spec.js',
    },
  ],
  webServer: [
    {
      command: 'python -m uvicorn main:app --host 127.0.0.1 --port 8000',
      cwd: path.join(__dirname, '..', 'backend'),
      url: 'http://127.0.0.1:8000/docs',
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        AUTH_DISABLED: 'false',
        GAIS_ADMIN_PASSWORD: 'Admin@123456!',
        RATE_LIMIT_DISABLED: 'true',
        GAIS_ALLOW_DEMO_SEED: 'true',
      },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      cwd: path.join(__dirname, '..', 'frontend'),
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
