import { apiClient } from '../client';
import { API_ENDPOINTS } from '../../constants';
import { User } from '../../types';
import { setAuthCookieFlag, clearAuthCookieFlag, hasAuthCookie } from './utils';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  id: string;
  name: string;
}

export const loginUser = async (username: string, password: string): Promise<User> => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  await apiClient.postForm<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, formData);

  // Set the auth flag before making the user info request
  setAuthCookieFlag();

  // Get user info - token is now in httpOnly cookie
  const userData = await apiClient.get<UserResponse>(API_ENDPOINTS.AUTH.ME);

  return {
    username: userData.name,
    id: userData.id,
  };
};

export const getCurrentUser = async (): Promise<User> => {
  const userData = await apiClient.get<UserResponse>(API_ENDPOINTS.AUTH.ME);

  return {
    username: userData.name,
    id: userData.id,
  };
};

export const checkAuthStatus = async (): Promise<User | null> => {
  // Skip API call if we know there's no auth cookie
  if (!hasAuthCookie()) {
    return null;
  }

  try {
    return await getCurrentUser();
  } catch (error) {
    // If the API call fails (e.g., expired token), clear the flag
    clearAuthCookieFlag();
    return null;
  }
};
