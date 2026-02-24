import type { GenreItemType, GenreKey } from '../types/song';

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
  pop: {
    label: 'POP',
    imageUrl: imgGenre4.src,
  },
  rock: {
    label: 'ROCK',
    imageUrl: imgGenre2.src,
  },
  rnb: {
    label: 'R&B',
    imageUrl: imgGenre3.src,
  },
  trot: {
    label: 'TROT',
    imageUrl: imgGenre1.src,
  },
  ballad: {
    label: 'BALLAD',
    imageUrl: imgGenre6.src,
  },
  dance: {
    label: 'DANCE',
    imageUrl: imgGenre5.src,
  },
};

export const GENRE_KEYS: GenreKey[] = ['pop', 'rock', 'rnb', 'trot', 'ballad', 'dance'];
