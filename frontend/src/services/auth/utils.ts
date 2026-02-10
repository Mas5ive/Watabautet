import { AUTH_STORAGE_KEY } from '../../constants';

/**
 * Check if the auth cookie exists.
 * This is a lightweight check that doesn't require an API call.
 */
export const hasAuthCookie = (): boolean => {
  return localStorage.getItem(AUTH_STORAGE_KEY) === 'true';
};

/**
 * Set the auth cookie flag in localStorage.
 * Call this after successful login.
 */
export const setAuthCookieFlag = (): void => {
  localStorage.setItem(AUTH_STORAGE_KEY, 'true');
};

/**
 * Clear the auth cookie flag in localStorage.
 * Call this after logout.
 */
export const clearAuthCookieFlag = (): void => {
  localStorage.removeItem(AUTH_STORAGE_KEY);
};
