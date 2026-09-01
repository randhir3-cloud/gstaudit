import { loginAndSaveToken } from './helpers/auth.js';

export default async function globalSetup() {
  await loginAndSaveToken('http://127.0.0.1:8000');
}
