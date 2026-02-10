import { apiClient } from '../client';
import { API_ENDPOINTS } from '../../constants';
import { User } from '../../types';
import { loginUser } from './login';

interface RegisterResponse {
  id: string;
  name: string;
}

export const registerUser = async (name: string, password: string): Promise<User> => {
  await apiClient.post<RegisterResponse>(API_ENDPOINTS.AUTH.SIGNUP, {
    name,
    password,
  });

  // After successful registration, automatically log in the user
  return await loginUser(name, password);
};
