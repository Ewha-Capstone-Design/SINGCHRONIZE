import { privateClient } from '@/shared/api/client';
import type {
  RecommendationCreateBody,
  RecommendationFeedbackBody,
  RecommendationStatusResponse,
} from '../model/types';

export const recommendationApi = {
  // POST: 추천 Job 생성
  create: async (
    body: RecommendationCreateBody = {},
  ): Promise<RecommendationStatusResponse> => {
    const { data, error } = await privateClient.POST('/api/v1/recommendations', {
      body,
    });
    if (error) throw error;
    return data as unknown as RecommendationStatusResponse;
  },

  // GET: 추천 Job 상태 및 결과 조회
  getStatus: async (jobId: string): Promise<RecommendationStatusResponse> => {
    const { data, error } = await privateClient.GET('/api/v1/recommendations/{job_id}', {
      params: { path: { job_id: jobId } },
    });
    if (error) throw error;
    return data as unknown as RecommendationStatusResponse;
  },

  // POST: 2차 추천을 위한 피드백 제출
  submitFeedback: async (
    jobId: string,
    feedback: RecommendationFeedbackBody,
  ): Promise<RecommendationStatusResponse> => {
    const { data, error } = await privateClient.POST(
      '/api/v1/recommendations/{job_id}/feedback',
      {
        params: { path: { job_id: jobId } },
        body: feedback,
      },
    );
    if (error) throw error;
    return data as unknown as RecommendationStatusResponse;
  },

  // GET: 최종 추천 결과 조회
  getSongs: async (jobId: string): Promise<RecommendationStatusResponse> => {
    const { data, error } = await privateClient.GET(
      '/api/v1/recommendations/{job_id}/songs',
      { params: { path: { job_id: jobId } } },
    );
    if (error) throw error;
    return data as unknown as RecommendationStatusResponse;
  },
};
