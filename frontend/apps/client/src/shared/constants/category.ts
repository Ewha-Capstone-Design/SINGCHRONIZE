import type { GenreKey, SituationKey } from '@/shared/types/category';
import { GENRE_ITEMS, GENRE_KEYS } from '@/shared/constants/genre';
import { SITUATION_ITEMS, SITUATION_KEYS } from '@/shared/constants/situation';

export type CategoryKey = GenreKey | SituationKey;

export type ArchiveCategoryMeta =
  | { type: 'genre'; key: GenreKey; label: string; imageUrl: string }
  | { type: 'situation'; key: SituationKey; label: string; imageUrl: string };

const isGenreKey = (key: string): key is GenreKey =>
  (GENRE_KEYS as string[]).includes(key);

const isSituationKey = (key: string): key is SituationKey =>
  (SITUATION_KEYS as string[]).includes(key);

export const getArchiveCategory = (key: string): ArchiveCategoryMeta | null => {
  if (isGenreKey(key)) {
    const item = GENRE_ITEMS[key];
    return { type: 'genre', key, label: item.tabLabel, imageUrl: item.imageUrl };
  }

  if (isSituationKey(key)) {
    const item = SITUATION_ITEMS[key];
    return { type: 'situation', key, label: item.label, imageUrl: item.imageUrl };
  }

  return null;
};
