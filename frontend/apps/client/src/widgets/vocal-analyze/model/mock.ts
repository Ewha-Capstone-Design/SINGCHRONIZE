import type { RecommendSongType, RecommendTab } from './types';

export const MOCK_SITUATION_TABS: RecommendTab<RecommendSongType>[] = [
  {
    key: 'drink',
    label: '회식 즐길 때',
    items: [
      {
        id: 1,
        title: 'Good Goodbye',
        artist: '화사 (HWASA)',
        tag: '발라드',
        bpm: 78,
        musicKey: 'D major',
        matchRate: 98,
        thumbnail: '',
        isLiked: true,
      },
      {
        id: 2,
        title: 'Good Goodbye',
        artist: '화사 (HWASA)',
        tag: '발라드',
        bpm: 78,
        musicKey: 'D major',
        matchRate: 98,
        thumbnail: '',
        isLiked: true,
      },
      {
        id: 3,
        title: 'Good Goodbye',
        artist: '화사 (HWASA)',
        tag: '발라드',
        bpm: 78,
        musicKey: 'D major',
        matchRate: 98,
        thumbnail: '',
        isLiked: false,
      },
    ],
  },
  { key: 'family', label: '가족과 함께', items: [] },
  { key: 'lover', label: '연인과 함께', items: [] },
];

export const MOCK_GENRE_TABS: RecommendTab<RecommendSongType>[] = [
  { key: 'all', label: '전체', items: [] },
  { key: 'pop', label: 'POP', items: [] },
  { key: 'ballad', label: '발라드', items: [] },
  { key: 'rnb', label: 'R&B', items: [] },
];
