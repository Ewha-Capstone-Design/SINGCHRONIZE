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
  label: string;
  imageUrl: string;
};
