import type { RankedSongType, SongApiType, SongUiType } from './types';
import { toSongUi } from './mapper';

export const MOCK_SONGS: SongApiType[] = [
  { id: '1', title: '밤편지', artist: '아이유', album_cover: null },
  { id: '2', title: 'The Action', artist: 'BOYNEXTDOOR', album_cover: null },
  { id: '3', title: 'Celebrity', artist: '아이유', album_cover: null },
];

export const MOCK_SONG_LIST: SongUiType[] = MOCK_SONGS.map(toSongUi);

export const MOCK_WEEKLY_CHART: RankedSongType[] = [
  {
    id: 1,
    rank: 1,
    title: 'SUPER REAL ME',
    artist: '아일릿(ILLIT)',
    thumbnail: '',
    likeCount: 2987,
    isLiked: false,
  },
  {
    id: 2,
    rank: 2,
    title: '자몽살구클럽',
    artist: '한로로',
    thumbnail: '',
    likeCount: 1927,
    isLiked: true,
  },
  {
    id: 3,
    rank: 3,
    title: 'Sunrise',
    artist: 'Tuesday Beach Club',
    thumbnail: '',
    likeCount: 875,
    isLiked: false,
  },
  {
    id: 4,
    rank: 4,
    title: 'Bye bye my blue',
    artist: '백예린 (Yerin Baek)',
    thumbnail: '',
    likeCount: 662,
    isLiked: false,
  },
];
