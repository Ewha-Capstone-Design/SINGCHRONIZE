import { isHistoryTag } from './tags';
import type { SongDataType } from '@/entities/song/model/types';
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

  const songData = item.song_data as unknown as SongDataType;

  return {
    historyId: item.id,
    title: songData?.name ?? '',
    artist: songData?.artist ?? '',
    thumbnail: songData?.album_image ?? undefined,
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
  coverImages: folder.thumbnails,
  songCount: folder.item_count,
  updatedAt: formatUpdatedAtLabel(folder.created_at),
});

export const toFavoriteSongUiType = (item: FavoriteSongApiType): FavoriteSongUiType => {
  const songData = item.song_data as unknown as SongDataType;
  return {
    itemId: item.id,
    songId: item.song_id,
    title: songData.name,
    artist: songData.artist,
    thumbnail: songData.album_image ?? undefined,
    isLiked: true,
  };
};
