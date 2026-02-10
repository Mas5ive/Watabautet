import { apiClient, handleResponse } from '../client';
import { API_ENDPOINTS, ERROR_MESSAGES } from '../../constants';
import { poll } from '../utils/polling';

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
  throw new Error(ERROR_MESSAGES.INVALID_URL);
};

export const startVideoProcessing = async (videoId: string): Promise<void> => {
  const response = await apiClient.fetch(API_ENDPOINTS.VIDEOS.PROCESS, {
    method: 'POST',
    body: JSON.stringify({ link: videoId }),
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (response.status !== 202 && !response.ok) {
    await handleResponse(response);
  }
};

export const pollVideoStatus = async (videoId: string): Promise<any> => {
  return poll(
    async () => {
      const response = await apiClient.fetch(`${API_ENDPOINTS.VIDEOS.LIST}/?link=${videoId}`);
      if (response.status === 200) {
        return { data: await response.json(), shouldContinue: false };
      }
      if (response.status !== 202) {
        await handleResponse(response);
      }
      return { data: null, shouldContinue: true };
    },
    undefined,
    undefined,
    ERROR_MESSAGES.VIDEO_TIMEOUT
  );
};

export const getVideoData = async (videoId: string): Promise<any> => {
  const response = await apiClient.fetch(`${API_ENDPOINTS.VIDEOS.LIST}/?link=${videoId}`);

  if (response.status === 200) {
    return await response.json();
  } else if (response.status === 202) {
    return await pollVideoStatus(videoId);
  } else if (response.status === 404) {
    await startVideoProcessing(videoId);
    return await pollVideoStatus(videoId);
  } else {
    return await handleResponse(response);
  }
};
