import { privateClient } from '@/shared/api/client';
import type { components } from '@singchronize/api';

export const homeApi = {
  // GET: 홈 피드 조회
  getHomeFeeds: async (): Promise<components['schemas']['HomeFeedsResponse']> => {
    const { data, error } = await privateClient.GET('/api/v1/home/feeds');
    if (error) throw error;
    return data;
  },
};
