import { ERROR_MESSAGES } from '../constants';

interface ApiError {
  detail?: string;
  message?: string;
}

export const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: ERROR_MESSAGES.UNKNOWN_ERROR }));
    const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }
  return response.json();
};

export const apiClient = {
  async get<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      ...options,
      method: 'GET',
      credentials: 'include',
    });
    return handleResponse<T>(response);
  },

  async post<T>(url: string, body?: any, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include',
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(response);
  },

  async postForm<T>(url: string, body: URLSearchParams, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        ...options.headers,
      },
      credentials: 'include',
      body: body.toString(),
    });
    return handleResponse<T>(response);
  },

  async delete<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      ...options,
      method: 'DELETE',
      credentials: 'include',
    });
    return handleResponse<T>(response);
  },

  // Special case for raw fetch when we need to handle status codes manually (like 202)
  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    return fetch(url, {
      credentials: 'include',
      ...options,
    });
  }
};
