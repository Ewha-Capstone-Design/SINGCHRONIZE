import type { SongApiType } from '@/entities/song/model/types';
import { HistoryTagType } from './tags';

export type HistoryItemApiType = {
  history_id: string;
  song: SongApiType;
  tags: string[];
  memo?: string | null;
  date: string; // "2026.02.15"
};

export type HistoryItemUiType = {
  historyId: string;
  title: string;
  artist: string;
  thumbnail?: string;
  tags: HistoryTagType[];
  memo?: string;
  date: string;
};
