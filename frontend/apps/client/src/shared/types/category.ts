export type SituationKey =
  | 'dinner'
  | 'family'
  | 'friend'
  | 'lover'
  | 'stage'
  | 'party'
  | 'mood'
  | 'ending';

export type SituationItemType = {
  label: string;
  imageUrl: string;
};

export type GenreKey = 'pop' | 'rock' | 'rnb' | 'trot' | 'ballad' | 'dance';

export type GenreItemType = {
  label: string; // 영문
  tabLabel: string; // 한글
  imageUrl: string;
};

export type CategoryKey = GenreKey | SituationKey;

export type CategoryMetaType =
  | { type: 'genre'; key: GenreKey; label: string; imageUrl: string }
  | { type: 'situation'; key: SituationKey; label: string; imageUrl: string };
