/** Attach JWT Authorization header to API requests in E2E tests. */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TOKEN_FILE = path.join(__dirname, '..', '.auth', 'token.json');

export const ADMIN_USERNAME = 'admin';
export const ADMIN_PASSWORD = 'Admin@123456!';

export async function loginAndSaveToken(baseURL = 'http://127.0.0.1:8000') {
  const res = await fetch(`${baseURL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: ADMIN_USERNAME, password: ADMIN_PASSWORD }),
  });
  if (!res.ok) throw new Error(`Login failed: ${res.status}`);
  const data = await res.json();
  fs.mkdirSync(path.dirname(TOKEN_FILE), { recursive: true });
  fs.writeFileSync(TOKEN_FILE, JSON.stringify({ access_token: data.access_token, user: data.user }));
  return data;
}

export function readAuthToken() {
  if (!fs.existsSync(TOKEN_FILE)) return null;
  return JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf-8')).access_token;
}

export function authHeaders() {
  const token = readAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Register auth token for all subsequent navigations in this page context. */
export async function ensureBrowserAuth(page) {
  const token = readAuthToken();
  if (!token) return;
  await page.addInitScript((t) => {
    localStorage.setItem('gais_access_token', t);
  }, token);
}

/** Set token after page has loaded (call after goto). */
export async function applyBrowserAuth(page) {
  const token = readAuthToken();
  if (!token) return;
  await page.evaluate((t) => localStorage.setItem('gais_access_token', t), token);
}

export async function prepareAuthenticatedPage(page, session = null) {
  await ensureBrowserAuth(page);
  await page.goto('/');
  if (session) {
    await page.evaluate((s) => localStorage.setItem('gst_audit_session', JSON.stringify(s)), session);
  }
  await applyBrowserAuth(page);
  await page.reload();
}
