import type { components } from '@singchronize/api';
import { HistoryTagType } from './tags';

export type HistoryItemApiType = components['schemas']['ArchiveResponse'];
export type FavoriteFolderApiType = components['schemas']['FolderResponse'];
export type FolderCreate = components['schemas']['FolderCreate'];
export type FavoriteSongApiType = components['schemas']['WishlistItemResponse'];
export type WishlistItemCreate = components['schemas']['WishlistItemCreate'];
export type ArchiveCreate = components['schemas']['ArchiveCreate'];
export type ArchiveUpdate = components['schemas']['ArchiveUpdate'];

export type HistoryItemUiType = {
  historyId: string;
  title: string;
  artist: string;
  thumbnail?: string;
  tags: HistoryTagType[];
  memo?: string;
  date: string;
};

export type FavoriteFolderUiType = {
  id: string;
  name: string;
  coverImages: string[];
  songCount: number;
  updatedAt: string;
};

export type FavoriteSongUiType = {
  itemId: string;
  songId: string;
  title: string;
  artist: string;
  thumbnail?: string;
  isLiked: boolean;
};
