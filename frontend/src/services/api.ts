import { User, SummaryResult, SummarySize, Language } from '../types';

// API base URL - will be proxied through Vite during development
// Backend API is mounted at /api/v1
const API_BASE_URL = '/api/v1';

interface RegisterResponse {
  id: string;
  name: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  id: string;
  name: string;
}

interface ApiError {
  detail: string;
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
};

export const registerUser = async (name: string, password: string): Promise<User> => {
  const response = await fetch(`${API_BASE_URL}/users/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name,
      password,
    }),
  });

  const userData: RegisterResponse = await handleResponse<RegisterResponse>(response);

  // After successful registration, automatically log in the user
  return await loginUser(name, password);
};

export const loginUser = async (username: string, password: string): Promise<User> => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/login/access-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  const tokenData: LoginResponse = await handleResponse<LoginResponse>(response);

  // Store the token for future requests
  localStorage.setItem('access_token', tokenData.access_token);

  // Get user info
  const userResponse = await fetch(`${API_BASE_URL}/users/me`, {
    headers: {
      'Authorization': `Bearer ${tokenData.access_token}`,
    },
  });

  const userData: UserResponse = await handleResponse<UserResponse>(userResponse);

  return {
    username: userData.name,
    id: userData.id,
  };
};

export const getCurrentUser = async (): Promise<User> => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('No authentication token found');
  }

  const response = await fetch(`${API_BASE_URL}/users/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    // Token is invalid or expired
    localStorage.removeItem('access_token');
    throw new Error('Invalid or expired token');
  }

  const userData: UserResponse = await handleResponse<UserResponse>(response);

  return {
    username: userData.name,
    id: userData.id,
  };
};

export const checkAuthStatus = async (): Promise<User | null> => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }

    // Try to get current user info
    const user = await getCurrentUser();
    return user;
  } catch (error) {
    // Token is invalid or expired, remove it
    localStorage.removeItem('access_token');
    return null;
  }
};