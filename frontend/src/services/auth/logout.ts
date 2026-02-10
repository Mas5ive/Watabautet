import { apiClient } from '../client';
import { API_ENDPOINTS } from '../../constants';
import { clearAuthCookieFlag } from './utils';

export const logoutUser = async (): Promise<void> => {
  // Clear the auth flag first for immediate UI update
  clearAuthCookieFlag();

  await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
};
