import { useQuery } from '@tanstack/react-query';
import { songApi } from '../api/songApi';
import { queryKeys } from '@/shared/api/queryKeys';
import { musicSearchResultToSongUi } from './mapper';

// GET: 곡 검색
export const useSearchMusic = (q: string) =>
  useQuery({
    queryKey: queryKeys.searchMusic(q),
    queryFn: () => songApi.searchMusic(q),
    select: (data) => data.map(musicSearchResultToSongUi),
    enabled: q.trim().length > 0,
  });
