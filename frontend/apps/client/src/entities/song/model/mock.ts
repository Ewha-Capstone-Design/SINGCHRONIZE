import type { RankedSongType, SongApiType, SongUiType } from './types';
import { toSongUi } from './mapper';

export const MOCK_SONGS: SongApiType[] = [
  {
    id: '1',
    title: '밤편지',
    artist: '아이유',
    album_cover: 'https://image.bugsm.co.kr/album/images/500/200890/20089092.jpg',
  },
  {
    id: '2',
    title: 'The Action',
    artist: 'BOYNEXTDOOR',
    album_cover:
      'https://i.namu.wiki/i/XV_vMrqtsdvkB5PSraNODxtPA4igk1jFCh09qLCjmMFYotOanmfVgrZKrxCW9Pn7GYA-Ez6nYL3DBxpD2qkddg.webp',
  },
  {
    id: '3',
    title: 'Celebrity',
    artist: '아이유',
    album_cover:
      'https://i.namu.wiki/i/p8XaoeIzcavxe0JHslIG7xXrRWiOGFfLIia3xRde6ukxJKn8g16N-KwPCssszNRCOU1mkv9Yu5n5Yu2nbnC20A.webp',
  },
];

export const MOCK_SONG_LIST: SongUiType[] = MOCK_SONGS.map(toSongUi);
