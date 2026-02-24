import type { SituationKey, SituationItemType } from '../types/song';

import imgKeyword1 from '@/shared/assets/images/situation/img_keyword_1.png';
import imgKeyword2 from '@/shared/assets/images/situation/img_keyword_2.png';
import imgKeyword3 from '@/shared/assets/images/situation/img_keyword_3.png';
import imgKeyword4 from '@/shared/assets/images/situation/img_keyword_4.png';
import imgKeyword5 from '@/shared/assets/images/situation/img_keyword_5.png';
import imgKeyword6 from '@/shared/assets/images/situation/img_keyword_6.png';
import imgKeyword7 from '@/shared/assets/images/situation/img_keyword_7.png';
import imgKeyword8 from '@/shared/assets/images/situation/img_keyword_8.png';

export const MAX_SITUATION_SELECT = 4;

export const SITUATION_ITEMS: Record<SituationKey, SituationItemType> = {
  dinner: {
    label: '회식하며\n즐길 때',
    imageUrl: imgKeyword1.src,
  },
  family: {
    label: '가족과\n함께할 때',
    imageUrl: imgKeyword8.src,
  },
  friend: {
    label: '친구랑\n놀 때',
    imageUrl: imgKeyword2.src,
  },
  lover: {
    label: '연인과\n함께할 때',
    imageUrl: imgKeyword3.src,
  },
  stage: {
    label: '공연을\n준비할 때',
    imageUrl: imgKeyword6.src,
  },
  party: {
    label: '신나게\n놀고 싶을 때',
    imageUrl: imgKeyword5.src,
  },
  mood: {
    label: '감성에\n젖고 싶을 때',
    imageUrl: imgKeyword7.src,
  },
  ending: {
    label: '엔딩곡이\n필요할 때',
    imageUrl: imgKeyword4.src,
  },
};

export const SITUATION_KEYS: SituationKey[] = [
  'dinner',
  'family',
  'friend',
  'lover',
  'stage',
  'party',
  'mood',
  'ending',
];
