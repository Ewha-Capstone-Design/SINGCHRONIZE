import type { SongApiType, SongUiType } from './types';

export const toSongUi = (song: SongApiType): SongUiType => ({
  id: String(song.id),
  title: song.title,
  artist: song.artist,
  thumbnail: song.album_cover ?? undefined,
});
