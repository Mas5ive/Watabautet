import { User, SummaryResult, SummarySize, Language, LibraryItem, LibraryEntry } from '../types';

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
    credentials: 'include', // Send/receive cookies
    body: formData.toString(),
  });

  await handleResponse<LoginResponse>(response);

  // Set the auth flag before making the user info request
  setAuthCookieFlag();

  // Get user info - token is now in httpOnly cookie
  const userResponse = await fetch(`${API_BASE_URL}/users/me`, {
    credentials: 'include', // Send cookies
  });

  const userData: UserResponse = await handleResponse<UserResponse>(userResponse);

  return {
    username: userData.name,
    id: userData.id,
  };
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await fetch(`${API_BASE_URL}/users/me`, {
    credentials: 'include', // Send cookies
  });

  if (!response.ok) {
    throw new Error('Not authenticated');
  }

  const userData: UserResponse = await handleResponse<UserResponse>(response);

  return {
    username: userData.name,
    id: userData.id,
  };
};

// Cookie name for authentication (must match backend config)
const AUTH_COOKIE_NAME = 'access_token';

/**
 * Check if the auth cookie exists.
 * This is a lightweight check that doesn't require an API call.
 */
const hasAuthCookie = (): boolean => {
  // Check if the cookie exists by trying to read it
  // document.cookie only shows cookies without HttpOnly flag, but we can check by setting a test cookie
  // Since access_token is httpOnly, we need a different approach
  
  // Alternative: Use a non-httpOnly cookie as a flag
  // For now, we'll use localStorage as a lightweight pre-check
  return localStorage.getItem('auth_present') === 'true';
};

/**
 * Set the auth cookie flag in localStorage.
 * Call this after successful login.
 */
export const setAuthCookieFlag = (): void => {
  localStorage.setItem('auth_present', 'true');
};

/**
 * Clear the auth cookie flag in localStorage.
 * Call this after logout.
 */
export const clearAuthCookieFlag = (): void => {
  localStorage.removeItem('auth_present');
};

export const checkAuthStatus = async (): Promise<User | null> => {
  // Skip API call if we know there's no auth cookie
  // This avoids unnecessary 401 requests on the home page
  if (!hasAuthCookie()) {
    return null;
  }
  
  try {
    const user = await getCurrentUser();
    return user;
  } catch (error) {
    // If the API call fails (e.g., expired token), clear the flag
    clearAuthCookieFlag();
    return null;
  }
};

export const logoutUser = async (): Promise<void> => {
  // Clear the auth flag first for immediate UI update
  clearAuthCookieFlag();
  
  await fetch(`${API_BASE_URL}/logout`, {
    method: 'POST',
    credentials: 'include', // Send cookies to clear them
  });
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

  const headers = {
    'Content-Type': 'application/json',
  };

  // 1. Ensure Video Data exists
  let videoData: any = null;
  try {
    const response = await fetch(`${API_BASE_URL}/videos/?link=${videoId}`, {
      headers,
      credentials: 'include', // Send cookies
    });
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
    const response = await fetch(summaryUrl, {
      headers,
      credentials: 'include', // Send cookies
    });

    if (response.status === 200) {
      const summaryData = await response.json();
      return formatSummaryResponse(summaryData, videoData.title, size, language, videoId);
    } else if (response.status === 202) {
      // Summary generation in progress
      const summaryData = await pollSummaryStatus(videoId, backendSize, language, headers);
      return formatSummaryResponse(summaryData, videoData.title, size, language, videoId);
    } else if (response.status === 404) {
      // Summary not found, start processing
      await startSummaryProcessing(videoId, backendSize, language, headers);
      const summaryData = await pollSummaryStatus(videoId, backendSize, language, headers);
      return formatSummaryResponse(summaryData, videoData.title, size, language, videoId);
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
    const response = await fetch(`${API_BASE_URL}/videos/?link=${videoId}`, {
      headers,
      credentials: 'include', // Send cookies
    });
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
    credentials: 'include', // Send cookies
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
    const response = await fetch(summaryUrl, {
      headers,
      credentials: 'include', // Send cookies
    });
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
    credentials: 'include', // Send cookies
    body: JSON.stringify({ video_link: videoId, size, language }),
  });
  if (response.status !== 202) {
    await handleResponse(response);
  }
};

const formatSummaryResponse = (data: any, title: string, size: SummarySize, language: Language, videoId?: string): SummaryResult => {
  // Backend returns text as a single string, frontend expects string[]
  const content = data.text ? data.text.split('\n').filter((p: string) => p.trim() !== '') : [];
  return {
    title: title || 'VIDEO SUMMARY',
    content,
    size,
    language,
    videoId,
  };
};

// --- Library Functions ---

const getAuthHeaders = () => {
  return {
    'Content-Type': 'application/json',
  };
};

export const saveToLibrary = async (summary: SummaryResult, videoId: string): Promise<void> => {
  const headers = getAuthHeaders();
  const backendSize = SIZE_MAPPING[summary.size];

  // 1. Save video to database
  const videoResponse = await fetch(`${API_BASE_URL}/videos/store`, {
    method: 'POST',
    headers,
    credentials: 'include', // Send cookies
    body: JSON.stringify({ link: videoId }),
  });

  // Ignore if video already exists (200) or handle other errors
  if (!videoResponse.ok && videoResponse.status !== 200) {
    await handleResponse(videoResponse);
  }

  // 2. Save summary to database
  const summaryResponse = await fetch(`${API_BASE_URL}/summaries/store`, {
    method: 'POST',
    headers,
    credentials: 'include', // Send cookies
    body: JSON.stringify({
      video_link: videoId,
      size: backendSize,
      language: summary.language,
    }),
  });

  // Ignore if summary already exists (200) or handle other errors
  if (!summaryResponse.ok && summaryResponse.status !== 200) {
    await handleResponse(summaryResponse);
  }

  // 3. Link summary to user
  const userResponse = await fetch(`${API_BASE_URL}/users/me/summaries`, {
    method: 'POST',
    headers,
    credentials: 'include', // Send cookies
    body: JSON.stringify({
      video_link: videoId,
      size: backendSize,
      language: summary.language,
    }),
  });

  await handleResponse(userResponse);
};

export const getLibrary = async (): Promise<LibraryItem[]> => {
  const headers = getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/users/me/library`, {
    headers,
    credentials: 'include', // Send cookies
  });
  const libraryData = await handleResponse<any>(response);

  // Transform backend data to frontend format
  return libraryData.videos.map((video: any) => {
    const entries: LibraryEntry[] = video.summaries.map((summary: any) => ({
      size: reverseSizeMapping[summary.size],
      language: summary.language as Language,
      content: summary.text ? summary.text.split('\n').filter((p: string) => p.trim() !== '') : [],
    }));

    return {
      id: `lib-${video.link}`,
      videoId: video.link,
      title: video.title,
      entries,
    };
  });
};

export const deleteSummary = async (videoId: string, size: SummarySize, language: Language): Promise<void> => {
  const headers = getAuthHeaders();
  const backendSize = SIZE_MAPPING[size];

  const response = await fetch(`${API_BASE_URL}/users/me/summaries?video_link=${videoId}&size=${backendSize}&language=${language}`, {
    method: 'DELETE',
    headers,
    credentials: 'include', // Send cookies
  });

  await handleResponse(response);
};

const reverseSizeMapping: Record<string, SummarySize> = {
  'small': SummarySize.SHORT,
  'medium': SummarySize.MEDIUM,
  'large': SummarySize.LONG,
};
