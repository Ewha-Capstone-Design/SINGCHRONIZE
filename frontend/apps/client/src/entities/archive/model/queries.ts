import { useQuery } from '@tanstack/react-query';
import { archiveApi } from '../api/archiveApi';
import { queryKeys } from '@/shared/api/queryKeys';
import { toArchiveRecItemUi, toArchiveItemFromSong } from './mapper';

type ArchiveParams = {
  genre?: string;
  keyword?: string;
  date?: string;
};

// GET: 추천 아카이브 조회
export const useRecommendationArchive = (params: ArchiveParams = {}) =>
  useQuery({
    queryKey: queryKeys.recommendationArchive(params),
    queryFn: () => archiveApi.getRecommendationArchive(params),
    select: (data) => ({
      groups: data.groups.flatMap((group) => group.items.map(toArchiveRecItemUi)),
      total: data.total,
    }),
  });

// GET: 홈 아카이브 프리뷰 조회
export const useArchivePreview = (genre?: string) =>
  useQuery({
    queryKey: queryKeys.recommendationArchive({ genre }),
    queryFn: () => archiveApi.getRecommendationArchive({ genre, size: 10 }),
    select: (data) => ({
      items: data.groups.flatMap((g) =>
        g.items.flatMap((item) => item.songs.map(toArchiveItemFromSong)),
      ),
      genreLabels: [
        ...new Set(
          data.groups.flatMap((g) =>
            g.items.flatMap((item) => item.selected_genre ?? []),
          ),
        ),
      ] as string[],
    }),
  });
