import type { HistoryItemApiType } from './types';
import { toHistoryItemUi } from './mapper';

const MOCK_HISTORY_ITEMS_API: HistoryItemApiType[] = [
  {
    history_id: 'h1',
    song: {
      id: 's1',
      title:
        '전체적으로 리듬은 잘 맞았고 초반 흐름도 안정적이었음. 다만 후반부로 갈수록 호흡이 부족해지면서 음정',
      artist: '박효신',
      album_cover: '',
    },
    tags: ['AGAIN', 'PRACTICE'],
    memo: '전체적으로 리듬은 잘 맞았고 초반 흐름도 안정적이었음. 다만 후반부로 갈수록 호흡이 부족해지면서 음정이 점점 흔들렸음. 특히 고음 구간에서 목에 힘이 들어가 소리가 얇아지고 답답하게 들렸음. 녹음으로 다시 들어보니 발음이 뭉개지는 부분도 있었고, 감정 표현이 일정하지 않았음. 다음에는 호흡을 더 길게 가져가고 고음 파트를 따로 나눠 연습할 필요가 있음. 전체적으로 힘을 빼고 부르는 연습도 같이 해보면 좋을 것 같음.',
    date: '2026.02.15',
  },
  {
    history_id: 'h2',
    song: {
      id: 's2',
      title: '밤편지',
      artist: '아이유',
      album_cover: '',
    },
    tags: ['COMFORTABLE'],
    memo: null,
    date: '2026.02.10',
  },
  {
    history_id: 'h3',
    song: {
      id: 's3',
      title: '사건의 지평선',
      artist: '윤하',
      album_cover: '',
    },
    tags: ['BAD_CONDITION', 'NOT_MY_STYLE'],
    memo: '키가 높아서 힘들었음',
    date: '2026.02.03',
  },
];

export const MOCK_HISTORY_ITEMS = MOCK_HISTORY_ITEMS_API.map(toHistoryItemUi);
