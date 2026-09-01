import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const PURCHASE_REGISTER_B64 = fs.readFileSync(path.join(__dirname, 'purchase_register.b64'), 'utf8').trim();
export const GSTR2A_COMPARISON_B64 = fs.readFileSync(path.join(__dirname, 'gstr2a_comparison.b64'), 'utf8').trim();
