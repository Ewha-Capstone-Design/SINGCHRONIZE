import { useQuery } from '@tanstack/react-query';
import { homeApi } from '../api/homeApi';
import { queryKeys } from '@/shared/api/queryKeys';
import { toWeeklySongUi, toLiveTickerBuskingUi } from './mapper';

// GET: 홈 피드 조회
export const useHomeFeeds = () =>
  useQuery({
    queryKey: queryKeys.homeFeeds,
    queryFn: () => homeApi.getHomeFeeds(),
    select: (data) => ({
      weekly: data.weekly.map(toWeeklySongUi),
      liveTicker: data.live_ticker.map(toLiveTickerBuskingUi),
    }),
  });
