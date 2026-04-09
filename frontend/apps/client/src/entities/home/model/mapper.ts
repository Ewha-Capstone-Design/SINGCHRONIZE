import type { WeeklySongApiType } from './types';
import type { RankedSongType } from '@/entities/song/model/types';

export const toWeeklySongUi = (song: WeeklySongApiType): RankedSongType => ({
  id: song.uri ?? song.rank,
  rank: song.rank,
  title: song.name,
  artist: song.artist,
  thumbnail: song.album_image ?? undefined,
  likeCount: song.wish_count,
  isLiked: false,
});
