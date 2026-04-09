import type { WeeklySongApiType, LiveTickerItemType } from './types';
import type { RankedSongType } from '@/entities/song';
import type { BuskingUiType } from '@/entities/busking';

export const toLiveTickerBuskingUi = (item: LiveTickerItemType): BuskingUiType => ({
  id: item.room_id,
  status: 'live',
  thumbnail: item.thumbnail ?? null,
  nickname: item.title,
  profileImage: '',
  totalViewers: item.viewer_count,
});

export const toWeeklySongUi = (song: WeeklySongApiType): RankedSongType => ({
  id: song.uri ?? song.rank,
  rank: song.rank,
  title: song.name,
  artist: song.artist,
  thumbnail: song.album_image ?? undefined,
  likeCount: song.wish_count,
  isLiked: false, // TODO: API 수정 필요
});
