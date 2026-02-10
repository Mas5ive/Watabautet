import { apiClient, handleResponse } from '../client';
import { API_ENDPOINTS, ERROR_MESSAGES, SIZE_MAPPING } from '../../constants';
import { SummaryResult, SummarySize, Language } from '../../types';
import { poll } from '../utils/polling';
import { getVideoData, extractVideoId } from '../video/video';

export const startSummaryProcessing = async (videoId: string, size: string, language: string): Promise<void> => {
  const response = await apiClient.fetch(API_ENDPOINTS.SUMMARIES.PROCESS, {
    method: 'POST',
    body: JSON.stringify({ video_link: videoId, size, language }),
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (response.status !== 202 && !response.ok) {
    await handleResponse(response);
  }
};

export const pollSummaryStatus = async (videoId: string, size: string, language: string): Promise<any> => {
  const summaryUrl = `${API_ENDPOINTS.SUMMARIES.LIST}/?video_link=${videoId}&size=${size}&language=${language}`;
  return poll(
    async () => {
      const response = await apiClient.fetch(summaryUrl);
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
    ERROR_MESSAGES.SUMMARY_TIMEOUT
  );
};

const formatSummaryResponse = (data: any, title: string, size: SummarySize, language: Language, videoId?: string): SummaryResult => {
  const content = data.text ? data.text.split('\n').filter((p: string) => p.trim() !== '') : [];
  return {
    title: title || 'VIDEO SUMMARY',
    content,
    size,
    language,
    videoId,
  };
};

export const extractSummary = async (
  url: string,
  size: SummarySize,
  language: Language
): Promise<SummaryResult> => {
  const videoId = extractVideoId(url);
  const backendSize = SIZE_MAPPING[size];

  try {
    // 1. Ensure Video Data exists
    const videoData = await getVideoData(videoId);

    // 2. Ensure Summary exists
    const summaryUrl = `${API_ENDPOINTS.SUMMARIES.LIST}/?video_link=${videoId}&size=${backendSize}&language=${language}`;
    const response = await apiClient.fetch(summaryUrl);

    if (response.status === 200) {
      const summaryData = await response.json();
      return formatSummaryResponse(summaryData, videoData.title, size, language, videoId);
    } else if (response.status === 202) {
      const summaryData = await pollSummaryStatus(videoId, backendSize, language);
      return formatSummaryResponse(summaryData, videoData.title, size, language, videoId);
    } else if (response.status === 404) {
      await startSummaryProcessing(videoId, backendSize, language);
      const summaryData = await pollSummaryStatus(videoId, backendSize, language);
      return formatSummaryResponse(summaryData, videoData.title, size, language, videoId);
    } else {
      await handleResponse(response);
      throw new Error(ERROR_MESSAGES.SUMMARY_FAILED);
    }
  } catch (error: any) {
    if (error.message === ERROR_MESSAGES.VIDEO_TIMEOUT || error.message === ERROR_MESSAGES.SUMMARY_TIMEOUT) {
      throw error;
    }
    throw new Error(error.message || ERROR_MESSAGES.SUMMARY_FAILED);
  }
};
