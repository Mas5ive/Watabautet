import { apiClient, handleResponse } from '../client';
import { API_ENDPOINTS, SIZE_MAPPING, REVERSE_SIZE_MAPPING } from '../../constants';
import { SummaryResult, SummarySize, Language, LibraryItem, LibraryEntry } from '../../types';

export const saveToLibrary = async (summary: SummaryResult, videoId: string): Promise<void> => {
  const backendSize = SIZE_MAPPING[summary.size];

  // 1. Save video to database
  const videoResponse = await apiClient.fetch(API_ENDPOINTS.VIDEOS.STORE, {
    method: 'POST',
    body: JSON.stringify({ link: videoId }),
    headers: { 'Content-Type': 'application/json' },
  });

  // Ignore if video already exists (200) or handle other errors
  if (!videoResponse.ok && videoResponse.status !== 200) {
    await handleResponse(videoResponse);
  }

  // 2. Save summary to database
  const summaryResponse = await apiClient.fetch(API_ENDPOINTS.SUMMARIES.STORE, {
    method: 'POST',
    body: JSON.stringify({
      video_link: videoId,
      size: backendSize,
      language: summary.language,
    }),
    headers: { 'Content-Type': 'application/json' },
  });

  // Ignore if summary already exists (200) or handle other errors
  if (!summaryResponse.ok && summaryResponse.status !== 200) {
    await handleResponse(summaryResponse);
  }

  // 3. Link summary to user
  await apiClient.post(API_ENDPOINTS.LIBRARY.USER_SUMMARIES, {
    video_link: videoId,
    size: backendSize,
    language: summary.language,
  });
};

export const getLibrary = async (): Promise<LibraryItem[]> => {
  const libraryData = await apiClient.get<any>(API_ENDPOINTS.LIBRARY.USER_LIBRARY);

  // Transform backend data to frontend format
  return libraryData.videos.map((video: any) => {
    const entries: LibraryEntry[] = video.summaries.map((summary: any) => ({
      size: REVERSE_SIZE_MAPPING[summary.size],
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
  const backendSize = SIZE_MAPPING[size];
  const url = `${API_ENDPOINTS.LIBRARY.USER_SUMMARIES}?video_link=${videoId}&size=${backendSize}&language=${language}`;
  
  await apiClient.delete(url);
};
