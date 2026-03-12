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

export interface FavoriteFolderApiType {
  id: string;
  name: string;
  thumbnail?: string[];
  count: number;
  updated_at: string;
}

export interface FavoriteFoldersResponse {
  folders: FavoriteFolderApiType[];
}

export interface FavoriteFolderUiType {
  id: string;
  name: string;
  coverImages: string[];
  songCount: number;
  updatedAt: string;
}

export interface FavoriteSongApiType {
  item_id: string;
  song: SongApiType;
  is_liked: boolean;
}

export interface FavoriteSongsResponse {
  items: FavoriteSongApiType[];
}

export interface FavoriteSongUiType {
  itemId: string;
  songId: string;
  title: string;
  artist: string;
  thumbnail?: string;
  isLiked: boolean;
}
