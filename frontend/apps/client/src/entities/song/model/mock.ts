import type { SongApiType, SongUiType } from './types';
import { toSongUi } from './mapper';

export const MOCK_SONGS: SongApiType[] = [
  { id: '1', title: '밤편지', artist: '아이유', album_cover: null },
  { id: '2', title: 'The Action', artist: 'BOYNEXTDOOR', album_cover: null },
  { id: '3', title: 'Celebrity', artist: '아이유', album_cover: null },
];

export const MOCK_SONG_LIST: SongUiType[] = MOCK_SONGS.map(toSongUi);
