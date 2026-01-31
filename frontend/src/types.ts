export enum SummarySize {
  SHORT = 'Essence',
  MEDIUM = 'Theses',
  LONG = 'Longread'
}

export type Language = 'EN' | 'RU';

export interface User {
  username: string;
}

export interface SummaryResult {
  title: string;
  content: string[];
  size: SummarySize;
  language: Language;
}

export interface LibraryEntry {
  size: SummarySize;
  language: Language;
  content: string[];
}

export interface LibraryItem {
  id: string;
  videoId: string;
  title: string;
  entries: LibraryEntry[]; // Replaces the old availableSizes map to support multiple langs per size
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
}

export type ModalType = 'none' | 'login' | 'register' | 'result';