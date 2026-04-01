import { privateClient } from '@/shared/api/client';
import type { MusicSearchResultType } from '../model/types';

export const songApi = {
  // GET: 곡 검색
  searchMusic: async (q: string): Promise<MusicSearchResultType[]> => {
    const { data, error } = await privateClient.GET('/api/v1/music/search', {
      params: { query: { q } },
    });
    if (error) throw error;
    return (data as MusicSearchResultType[]) ?? [];
  },
};
