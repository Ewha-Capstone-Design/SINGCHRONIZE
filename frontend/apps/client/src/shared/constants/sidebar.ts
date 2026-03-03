import {
  IcHome,
  IcAnalyze,
  IcLive,
  IcSing,
  IcLibrary,
  IcMy,
} from '@/shared/assets/icons';

export const SIDEBAR_ITEMS = [
  { id: 'home', label: '홈', Icon: IcHome, href: '/home' },
  { id: 'recommend', label: '보컬 분석', Icon: IcAnalyze, href: '/recommend' },
  { id: 'live', label: '온라인 버스킹', Icon: IcLive, href: '/live' },
  { id: 'library', label: '노래방 키트', Icon: IcSing, href: '/library' },
  { id: 'archive', label: '아카이브', Icon: IcLibrary, href: '/archive' },
  { id: 'my', label: '마이페이지', Icon: IcMy, href: '/my' },
] as const;
