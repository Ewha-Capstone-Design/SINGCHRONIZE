import { GENRE_ITEMS, GENRE_KEYS } from '@/shared/constants/genre';
import { SITUATION_ITEMS, SITUATION_KEYS } from '@/shared/constants/situation';
import type { SongApiType } from '@/entities/song';
import type { RecommendSongType, RecommendTab } from '@/widgets/vocal-analyze/model';

const GENRE_KEY_SET = new Set<string>(GENRE_KEYS);
const SITUATION_KEY_SET = new Set<string>(SITUATION_KEYS);

export const toRecommendSong = (song: SongApiType): RecommendSongType => ({
  id: song.id,
  title: song.title,
  artist: song.artist,
  thumbnail: song.album_cover ?? undefined,
});

const toSituationTab = (
  key: string,
  songs: SongApiType[],
): RecommendTab<RecommendSongType> => ({
  key,
  label:
    SITUATION_ITEMS[key as keyof typeof SITUATION_ITEMS]?.label.replace('\n', ' ') ?? key,
  items: songs.map(toRecommendSong),
});

const toGenreTab = (
  key: string,
  songs: SongApiType[],
): RecommendTab<RecommendSongType> => ({
  key,
  label: GENRE_ITEMS[key as keyof typeof GENRE_ITEMS]?.tabLabel ?? key,
  items: songs.map(toRecommendSong),
});

// recommended_songs를 상황별/장르별 탭으로 변환
export const buildRecommendTabs = (
  recommended: Record<string, SongApiType[]>,
): {
  situationTabs: RecommendTab<RecommendSongType>[];
  genreTabs: RecommendTab<RecommendSongType>[];
} => {
  const hasSituations = typeof recommended['situations'] === 'object';
  const hasGenres = typeof recommended['genres'] === 'object';

  if (hasSituations || hasGenres) {
    const situationData = (recommended['situations'] ?? {}) as Record<
      string,
      SongApiType[]
    >;
    const genreData = (recommended['genres'] ?? {}) as Record<string, SongApiType[]>;
    return {
      situationTabs: Object.entries(situationData).map(([k, v]) => toSituationTab(k, v)),
      genreTabs: Object.entries(genreData).map(([k, v]) => toGenreTab(k, v)),
    };
  }

  const situationTabs: RecommendTab<RecommendSongType>[] = [];
  const genreTabs: RecommendTab<RecommendSongType>[] = [];

  for (const [key, songs] of Object.entries(recommended)) {
    const items = Array.isArray(songs) ? songs : [];
    if (SITUATION_KEY_SET.has(key)) {
      situationTabs.push(toSituationTab(key, items));
    } else {
      genreTabs.push(
        GENRE_KEY_SET.has(key)
          ? toGenreTab(key, items)
          : { key, label: key, items: items.map(toRecommendSong) },
      );
    }
  }

  return { situationTabs, genreTabs };
};
