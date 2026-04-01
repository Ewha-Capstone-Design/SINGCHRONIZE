import { useQuery } from '@tanstack/react-query';
import { singerApi } from '../api/singerApi';
import { queryKeys } from '@/shared/api/queryKeys';
import { toArtistUi } from './mapper';

// GET: 가수 검색
export const useSearchSingers = (q: string, limit?: number) =>
  useQuery({
    queryKey: queryKeys.searchSingers(q),
    queryFn: () => singerApi.searchSingers(q, limit),
    select: (data) => data.map(toArtistUi),
    enabled: q.trim().length > 0,
  });

// GET: 랜덤 가수 목록
export const useRandomSingers = (gender: string, limit?: number) =>
  useQuery({
    queryKey: queryKeys.randomSingers(gender),
    queryFn: () => singerApi.getRandomSingers(gender, limit),
    select: (data) => data.map(toArtistUi),
  });
