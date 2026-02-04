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
  detail?: string;
  message?: string;
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
    const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
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

export const logoutUser = async (): Promise<void> => {
  localStorage.removeItem('access_token');
};

/**
 * Extracts the 11-character YouTube video ID from various URL formats.
 */
export const extractVideoId = (url: string): string => {
  const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/i;
  const match = url.match(regex);
  if (match && match[1]) {
    return match[1];
  }
  // If it's already an 11-char ID, return it
  if (url.length === 11 && /^[a-zA-Z0-9_-]{11}$/.test(url)) {
    return url;
  }
  throw new Error('INVALID YOUTUBE URL. FEED THE MACHINE A VALID LINK.');
};

const SIZE_MAPPING: Record<SummarySize, string> = {
  [SummarySize.SHORT]: 'small',
  [SummarySize.MEDIUM]: 'medium',
  [SummarySize.LONG]: 'large',
};

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const extractSummary = async (
  url: string,
  size: SummarySize,
  language: Language
): Promise<SummaryResult> => {
  const videoId = extractVideoId(url);
  const backendSize = SIZE_MAPPING[size];
  const token = localStorage.getItem('access_token');

  if (!token) {
    throw new Error('AUTHENTICATION REQUIRED. LOG IN TO PROCEED.');
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // 1. Ensure Video Data exists
  let videoData: any = null;
  try {
    const response = await fetch(`${API_BASE_URL}/videos/?link=${videoId}`, { headers });
    if (response.status === 200) {
      videoData = await response.json();
    } else if (response.status === 202) {
      // Video processing in progress
      videoData = await pollVideoStatus(videoId, headers);
    } else if (response.status === 404) {
      // Video not found, start processing
      await startVideoProcessing(videoId, headers);
      videoData = await pollVideoStatus(videoId, headers);
    } else {
      await handleResponse(response); // Will throw error
    }
  } catch (error: any) {
    throw new Error(error.message || 'FAILED TO PROCESS VIDEO DATA.');
  }

  // 2. Ensure Summary exists
  try {
    const summaryUrl = `${API_BASE_URL}/summaries/?video_link=${videoId}&size=${backendSize}&language=${language}`;
    const response = await fetch(summaryUrl, { headers });

    if (response.status === 200) {
      const summaryData = await response.json();
      return formatSummaryResponse(summaryData, videoData.title, size, language);
    } else if (response.status === 202) {
      // Summary generation in progress
      const summaryData = await pollSummaryStatus(videoId, backendSize, language, headers);
      return formatSummaryResponse(summaryData, videoData.title, size, language);
    } else if (response.status === 404) {
      // Summary not found, start processing
      await startSummaryProcessing(videoId, backendSize, language, headers);
      const summaryData = await pollSummaryStatus(videoId, backendSize, language, headers);
      return formatSummaryResponse(summaryData, videoData.title, size, language);
    } else {
      await handleResponse(response); // Will throw error
    }
  } catch (error: any) {
    throw new Error(error.message || 'FAILED TO GENERATE SUMMARY.');
  }

  throw new Error('UNEXPECTED STATE IN SUMMARY EXTRACTION.');
};

const pollVideoStatus = async (videoId: string, headers: any): Promise<any> => {
  const maxAttempts = 60; // 2 minutes with 2s delay
  for (let i = 0; i < maxAttempts; i++) {
    await delay(2000);
    const response = await fetch(`${API_BASE_URL}/videos/?link=${videoId}`, { headers });
    if (response.status === 200) {
      return response.json();
    }
    if (response.status !== 202) {
      await handleResponse(response);
    }
  }
  throw new Error('VIDEO PROCESSING TIMED OUT.');
};

const startVideoProcessing = async (videoId: string, headers: any) => {
  const response = await fetch(`${API_BASE_URL}/videos/process`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ link: videoId }),
  });
  if (response.status !== 202) {
    await handleResponse(response);
  }
};

const pollSummaryStatus = async (videoId: string, size: string, language: string, headers: any): Promise<any> => {
  const maxAttempts = 60;
  const summaryUrl = `${API_BASE_URL}/summaries/?video_link=${videoId}&size=${size}&language=${language}`;
  for (let i = 0; i < maxAttempts; i++) {
    await delay(2000);
    const response = await fetch(summaryUrl, { headers });
    if (response.status === 200) {
      return response.json();
    }
    if (response.status !== 202) {
      await handleResponse(response);
    }
  }
  throw new Error('SUMMARY GENERATION TIMED OUT.');
};

const startSummaryProcessing = async (videoId: string, size: string, language: string, headers: any) => {
  const response = await fetch(`${API_BASE_URL}/summaries/process`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ video_link: videoId, size, language }),
  });
  if (response.status !== 202) {
    await handleResponse(response);
  }
};

const formatSummaryResponse = (data: any, title: string, size: SummarySize, language: Language): SummaryResult => {
  // Backend returns text as a single string, frontend expects string[]
  const content = data.text ? data.text.split('\n').filter((p: string) => p.trim() !== '') : [];
  return {
    title: title || 'VIDEO SUMMARY',
    content,
    size,
    language,
  };
};
