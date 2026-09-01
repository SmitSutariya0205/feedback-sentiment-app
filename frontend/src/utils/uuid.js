import { v4 as uuidv4, validate as uuidValidate } from 'uuid';

/**
 * Generate a new UUID v4 string for end-to-end request tracing.
 */
export function generateRequestId() {
  return uuidv4();
}

/**
 * Validate if a given string is a valid UUID v4.
 */
export function isValidUuid(str) {
  return typeof str === 'string' && uuidValidate(str);
}
