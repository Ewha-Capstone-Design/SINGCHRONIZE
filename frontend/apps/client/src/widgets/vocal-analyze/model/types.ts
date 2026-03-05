import type { SongUiType } from '@/entities/song/model/types';

export type RecommendTab<T> = {
  key: string;
  label: string;
  items: T[];
};

export type RecommendSongType = SongUiType & {
  tag?: string;
  bpm?: number;
  musicKey?: string;
  matchRate?: number;
  rank?: number;
};
