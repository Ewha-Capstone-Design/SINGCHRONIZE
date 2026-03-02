import { isHistoryTag } from './tags';
import { HistoryItemApiType, HistoryItemUiType } from './types';

export const toHistoryItemUi = (item: HistoryItemApiType): HistoryItemUiType => ({
  historyId: item.history_id,
  title: item.song.title,
  artist: item.song.artist ?? '',
  thumbnail: item.song.album_cover ?? undefined,
  tags: (item.tags ?? []).filter(isHistoryTag),
  memo: item.memo ?? undefined,
  date: item.date,
});
