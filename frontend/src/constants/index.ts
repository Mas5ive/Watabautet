import { SummarySize } from '../types';

// API Configuration
export const API_BASE_URL = '/api/v1';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/login/access-token`,
    LOGOUT: `${API_BASE_URL}/logout`,
    ME: `${API_BASE_URL}/users/me`,
    SIGNUP: `${API_BASE_URL}/users/signup`,
  },
  VIDEOS: {
    LIST: `${API_BASE_URL}/videos`,
    PROCESS: `${API_BASE_URL}/videos/process`,
    STORE: `${API_BASE_URL}/videos/store`,
  },
  SUMMARIES: {
    LIST: `${API_BASE_URL}/summaries`,
    PROCESS: `${API_BASE_URL}/summaries/process`,
    STORE: `${API_BASE_URL}/summaries/store`,
  },
  LIBRARY: {
    USER_LIBRARY: `${API_BASE_URL}/users/me/library`,
    USER_SUMMARIES: `${API_BASE_URL}/users/me/summaries`,
  },
} as const;

// Polling Configuration
export const POLLING = {
  MAX_ATTEMPTS: 60,
  DELAY_MS: 2000,
  TIMEOUT_MESSAGE: 'TIMEOUT',
} as const;

// Animation Durations (ms)
export const ANIMATION_DURATIONS = {
  FAST: 200,
  NORMAL: 300,
  SLOW: 500,
} as const;

// Size Mapping (Frontend enum to Backend string)
export const SIZE_MAPPING: Record<SummarySize, string> = {
  [SummarySize.SHORT]: 'small',
  [SummarySize.MEDIUM]: 'medium',
  [SummarySize.LONG]: 'large',
} as const;

// Reverse Size Mapping (Backend string to Frontend enum)
export const REVERSE_SIZE_MAPPING: Record<string, SummarySize> = {
  'small': SummarySize.SHORT,
  'medium': SummarySize.MEDIUM,
  'large': SummarySize.LONG,
} as const;

// Auth Configuration
export const AUTH_STORAGE_KEY = 'auth_present';
export const AUTH_COOKIE_NAME = 'access_token';

// Error Messages
export const ERROR_MESSAGES = {
  INVALID_URL: 'INVALID YOUTUBE URL. FEED THE MACHINE A VALID LINK.',
  VIDEO_TIMEOUT: 'VIDEO PROCESSING TIMED OUT.',
  SUMMARY_TIMEOUT: 'SUMMARY GENERATION TIMED OUT.',
  VIDEO_FAILED: 'FAILED TO PROCESS VIDEO DATA.',
  SUMMARY_FAILED: 'FAILED TO GENERATE SUMMARY.',
  NOT_AUTHENTICATED: 'Not authenticated',
  UNKNOWN_ERROR: 'UNKNOWN ERROR IN THE VOID.',
  NO_DATA: 'NO DATA DETECTED. FEED THE MACHINE.',
} as const;

// UI Configuration
export const UI = {
  DEBOUNCE_DELAY: 300,
  MAX_INPUT_LENGTH: 2048,
} as const;