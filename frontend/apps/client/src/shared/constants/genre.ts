import type { GenreItemType, GenreKey } from '../types/category';

import imgGenre1 from '@/shared/assets/images/genre/img_genre_1.png';
import imgGenre2 from '@/shared/assets/images/genre/img_genre_2.png';
import imgGenre3 from '@/shared/assets/images/genre/img_genre_3.png';
import imgGenre4 from '@/shared/assets/images/genre/img_genre_4.png';
import imgGenre5 from '@/shared/assets/images/genre/img_genre_5.png';
import imgGenre6 from '@/shared/assets/images/genre/img_genre_6.png';

export const MAX_GENRE_SELECT = 3;

export const STEP_GENRE_TEXT = {
  title: '좋아하는 장르를 선택해 주세요',
  desc: '최대 3개까지 선택 가능해요. 없으면 건너뛰어도 돼요',
} as const;

export const GENRE_ITEMS: Record<GenreKey, GenreItemType> = {
  ballad: { label: 'BALLAD', tabLabel: '발라드', imageUrl: imgGenre6.src },
  dance: { label: 'DANCE', tabLabel: '댄스', imageUrl: imgGenre5.src },
  pop: { label: 'POP', tabLabel: 'POP', imageUrl: imgGenre4.src },
  trot: { label: 'TROT', tabLabel: '트로트', imageUrl: imgGenre1.src },
  rock: { label: 'ROCK', tabLabel: '락·메탈', imageUrl: imgGenre2.src },
  rnb: { label: 'R&B', tabLabel: 'R&B', imageUrl: imgGenre3.src },
};

export const GENRE_API_LABEL: Record<GenreKey, string> = {
  ballad: '발라드',
  dance: '댄스',
  pop: 'POP',
  trot: '트로트',
  rock: '락/메탈',
  rnb: 'R&B',
};

export const GENRE_KEYS: GenreKey[] = ['ballad', 'dance', 'pop', 'trot', 'rock', 'rnb'];
