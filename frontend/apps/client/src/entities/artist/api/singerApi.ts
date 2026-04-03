import { privateClient } from '@/shared/api/client';
import type { ArtistApiType } from '../model/types';

export const singerApi = {
  // GET: 가수 검색
  searchSingers: async (q: string, limit?: number): Promise<ArtistApiType[]> => {
    const { data, error } = await privateClient.GET('/api/v1/singers/search', {
      params: { query: { q, ...(limit !== undefined && { limit }) } },
    });
    if (error) throw error;
    return data?.singers ?? [];
  },

  // GET: 랜덤 가수 목록 (gender 미입력 시 남자 6 + 여자 6)
  getRandomSingers: async (
    gender?: string | null,
    limit?: number,
  ): Promise<ArtistApiType[]> => {
    const { data, error } = await privateClient.GET('/api/v1/singers/random', {
      // @ts-expect-error: path-level schema에 query?: never 충돌 이슈
      params: { query: { gender, ...(limit !== undefined && { limit }) } },
    });
    if (error) throw error;
    return data?.singers ?? [];
  },
};
