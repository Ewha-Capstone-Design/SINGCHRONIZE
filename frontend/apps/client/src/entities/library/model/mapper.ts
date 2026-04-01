import { isHistoryTag } from './tags';
import type {
  FavoriteFolderApiType,
  FavoriteFolderUiType,
  FavoriteSongApiType,
  FavoriteSongUiType,
  HistoryItemApiType,
  HistoryItemUiType,
} from './types';

export const toHistoryItemUi = (item: HistoryItemApiType): HistoryItemUiType => {
  const date = new Date(item.recorded_date);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const formattedDate = `${year}.${month}.${day}`;

  return {
    historyId: item.id,
    title: item.song?.title ?? '',
    artist: item.song?.artist ?? '',
    thumbnail: item.song?.album_cover ?? undefined,
    tags: (item.tags ?? []).filter(isHistoryTag),
    memo: item.memo ?? undefined,
    date: formattedDate,
  };
};

const formatUpdatedAtLabel = (dateStr: string) => {
  const date = new Date(dateStr);
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
  folder: FavoriteFolderApiType,
): FavoriteFolderUiType => ({
  id: folder.id,
  name: folder.name,
  coverImages: [],
  songCount: folder.item_count,
  updatedAt: formatUpdatedAtLabel(folder.created_at),
});

export const toFavoriteSongUiType = (item: FavoriteSongApiType): FavoriteSongUiType => ({
  itemId: item.id,
  songId: item.song.id,
  title: item.song.title,
  artist: item.song.artist,
  thumbnail: item.song.album_cover ?? undefined,
  isLiked: true,
});
