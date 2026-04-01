import { privateClient } from '@/shared/api/client';
import type { ArtistApiType } from '../model/types';

export const singerApi = {
  // GET: 가수 검색
  searchSingers: async (q: string, limit?: number): Promise<ArtistApiType[]> => {
    const { data, error } = await privateClient.GET('/api/v1/singers/search', {
      params: { query: { q, ...(limit !== undefined && { limit }) } },
    })
    if (error) throw error;
    return data?.singers ?? [];
  },

  // GET: 랜덤 가수 목록
  getRandomSingers: async (gender: string, limit?: number): Promise<ArtistApiType[]> => {
    const { data, error } = await privateClient.GET('/api/v1/singers/random', {
      params: { query: { gender, ...(limit !== undefined && { limit }) } },
    });
    if (error) throw error;
    return data?.singers ?? [];
  },
};
