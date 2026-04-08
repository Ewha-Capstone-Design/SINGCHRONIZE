import { GENRE_ITEMS } from '@/shared/constants/genre';
import { SITUATION_ITEMS } from '@/shared/constants/situation';
import type { RecommendedSongItemType } from '@/entities/recommendation/model/types';
import type { RecommendSongType, RecommendTab } from '@/widgets/vocal-analyze/model';

const toRecommendSong = (song: RecommendedSongItemType): RecommendSongType => ({
  id: song.song_id,
  title: song.title,
  artist: song.artist,
  thumbnail: song.album_cover ?? undefined,
});

const toSituationTab = (
  key: string,
  songs: RecommendedSongItemType[],
): RecommendTab<RecommendSongType> => ({
  key,
  label:
    SITUATION_ITEMS[key as keyof typeof SITUATION_ITEMS]?.label.replace('\n', ' ') ?? key,
  items: songs.map(toRecommendSong),
});

const toGenreTab = (
  key: string,
  songs: RecommendedSongItemType[],
): RecommendTab<RecommendSongType> => ({
  key,
  label: GENRE_ITEMS[key as keyof typeof GENRE_ITEMS]?.tabLabel ?? key,
  items: songs.map(toRecommendSong),
});

// recommended_songs를 상황별/장르별 탭으로 변환
export const buildRecommendTabs = (recommended: {
  genre_recommendations?: Record<string, RecommendedSongItemType[]>;
  situation_recommendations?: Record<string, RecommendedSongItemType[]>;
}): {
  situationTabs: RecommendTab<RecommendSongType>[];
  genreTabs: RecommendTab<RecommendSongType>[];
} => ({
  situationTabs: Object.entries(recommended.situation_recommendations ?? {}).map(
    ([k, v]) => toSituationTab(k, v),
  ),
  genreTabs: Object.entries(recommended.genre_recommendations ?? {})
    .sort(([a], [b]) => (a === '전체' ? -1 : b === '전체' ? 1 : 0))
    .map(([k, v]) => toGenreTab(k, v)),
});
