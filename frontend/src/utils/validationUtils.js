export { isValidGSTIN, normalizeGSTIN } from './formatGSTIN';

export function required(value, fieldName = 'Field') {
  if (value == null || String(value).trim() === '') {
    return `${fieldName} is required`;
  }
  return null;
}
