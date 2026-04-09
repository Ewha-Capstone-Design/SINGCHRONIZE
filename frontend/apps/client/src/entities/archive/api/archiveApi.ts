import { privateClient } from '@/shared/api/client';
import type { RecommendationArchiveParams } from '../model/types';

export const archiveApi = {
  // GET: 추천 아카이브 조회
  getRecommendationArchive: async (params: RecommendationArchiveParams = {}) => {
    const { data, error } = await privateClient.GET(
      '/api/v1/library/history/recommendations',
      // @ts-expect-error: path-level schema에 query?: never 충돌 이슈
      { params: { query: params } },
    );
    if (error) throw error;
    return data;
  },
};
