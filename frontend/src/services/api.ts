import { User } from '../types';

// API base URL - will be proxied through Vite during development
// Backend API is mounted at /api/v1
const API_BASE_URL = '/api/v1';

interface RegisterResponse {
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

  return {
    username: userData.name,
    id: userData.id,
  };
};