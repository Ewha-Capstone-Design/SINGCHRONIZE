import { isHistoryTag } from './tags';
import {
  FavoriteFolderApiType,
  FavoriteFolderUiType,
  FavoriteSongApiType,
  FavoriteSongUiType,
  HistoryItemApiType,
  HistoryItemUiType,
} from './types';

export const toHistoryItemUi = (item: HistoryItemApiType): HistoryItemUiType => ({
  historyId: item.history_id,
  title: item.song.title,
  artist: item.song.artist ?? '',
  thumbnail: item.song.album_cover ?? undefined,
  tags: (item.tags ?? []).filter(isHistoryTag),
  memo: item.memo ?? undefined,
  date: item.date,
});

const formatUpdatedAtLabel = (updatedAt: string) => {
  const date = new Date(updatedAt);
  const today = new Date();

  const isSameDate =
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate();

  if (isSameDate) return '오늘 업데이트';

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}.${month}.${day}`;
};

export const toFavoriteFolderUi = (
  folder: FavoriteFolderApiType
): FavoriteFolderUiType => ({
  id: folder.id,
  name: folder.name,
  coverImages: folder.thumbnail ?? [],
  songCount: folder.count,
  updatedAt: formatUpdatedAtLabel(folder.updated_at),
});

export const toFavoriteSongUiType = (item: FavoriteSongApiType): FavoriteSongUiType => ({
  itemId: item.item_id,
  songId: item.song.id,
  title: item.song.title,
  artist: item.song.artist,
  thumbnail: item.song.album_cover ?? undefined,
  isLiked: item.is_liked,
});
