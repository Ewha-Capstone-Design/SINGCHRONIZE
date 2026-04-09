import type {
  SongApiType,
  SongUiType,
  MusicSearchResultType,
  FirstRecommendedSongType,
} from './types';

export const toSongUi = (song: SongApiType): SongUiType => ({
  id: String(song.id),
  title: song.title,
  artist: song.artist,
  thumbnail: song.album_cover ?? undefined,
});

export const musicSearchResultToSongUi = (song: MusicSearchResultType): SongUiType => ({
  id: song.uri,
  title: song.name,
  artist: song.artist,
  thumbnail: song.album_image ?? undefined,
});

export const toFirstRecommendedSongUi = (song: FirstRecommendedSongType): SongUiType => ({
  id: song.song_id,
  title: song.title,
  artist: song.artist,
  thumbnail: song.album_cover ?? undefined,
});
