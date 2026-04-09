import type {
  ArchiveSectionUiType,
  ArchiveItemUiType,
  ArchiveSongApiType,
  ArchiveRecItemApiType,
} from './types';
import { getArchiveHistoryTitle } from './utils';

export const toArchiveRecItemUi = (
  item: ArchiveRecItemApiType,
): ArchiveSectionUiType => ({
  id: item.rec_id,
  title: getArchiveHistoryTitle(item.date),
  songs: item.songs.map((s) => ({
    id: s.song_id,
    title: s.title,
    artist: s.artist,
    thumbnail: s.album_cover ?? undefined,
  })),
});

export const toArchiveItemFromSong = (song: ArchiveSongApiType): ArchiveItemUiType => ({
  id: song.song_id,
  title: song.title,
  artist: song.artist,
  thumbnail: song.album_cover ?? null,
  matchRate: song.score != null ? Math.round(song.score * 100) : 0,
  isLiked: false, // TODO: API 수정 필요
});
