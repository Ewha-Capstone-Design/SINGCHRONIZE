import type { BuskingUiType, SetlistType, ChatMessageType } from './types';

export const MOCK_BUSKING_LIST: BuskingUiType[] = [
  {
    id: '1',
    status: 'live',
    thumbnail: '',
    nickname: '루드',
    listenerCount: 98,
    profileImage: '',
  },
  {
    id: '2',
    status: 'record',
    thumbnail: '',
    nickname: '루드',
    listenerCount: 54,
    profileImage: '',
  },
  {
    id: '3',
    status: 'live',
    thumbnail: '',
    profileImage: '',
    nickname: '유지니',
    listenerCount: 31,
  },
  {
    id: '4',
    status: 'live',
    thumbnail: '',
    profileImage: '',
    nickname: 'quuury28',
    listenerCount: 65,
  },
  {
    id: '5',
    status: 'record',
    thumbnail: '',
    profileImage: '',
    nickname: '김보라',
    listenerCount: 27,
  },
  {
    id: '6',
    status: 'record',
    thumbnail: '',
    profileImage: '',
    nickname: '소라',
    listenerCount: 98,
  },
  {
    id: '7',
    status: 'record',
    thumbnail: '',
    profileImage: '',
    nickname: '별사탕',
    listenerCount: 77,
  },
  {
    id: '8',
    status: 'live',
    thumbnail: '',
    profileImage: '',
    nickname: '김태진',
    listenerCount: 19,
  },
];

export const MOCK_SETLIST: SetlistType[] = [
  { rank: 1, title: '이상비행', artist: '한로로' },
  { rank: 2, title: '주저하는 연인들을 위해', artist: '잔나비', isCurrent: true },
  { rank: 3, title: '자몽살구클럽', artist: '한로로' },
  { rank: 4, title: '바이, 썸머', artist: '아이유' },
  { rank: 5, title: '파도', artist: '새소년' },
];

export const MOCK_CHAT: ChatMessageType[] = [
  { id: '1', username: '캐로로', message: '한로로 목소리랑 너무너무 잘어울려요ㅠㅠㅠㅠ' },
  { id: '2', username: 'zeeerl98', message: '아이유 노래도 기대됩니다아아아' },
  { id: '3', username: '노래조아25', message: '목소리 진짜 제 스타일 ㅠㅠㅠㅠㅠㅠㅠㅠ' },
  { id: '4', username: '1slfhhdds', message: '잘부르시는데 좀만 크게 부르서도 될듯?' },
  {
    id: '5',
    username: '세영이',
    message: '잔나비 노래 정말 좋아하는데 정말 잘어울리시거같아요 음원내주세용!!!!!',
  },
  { id: '6', username: '태훈', message: '최고입니다' },
  {
    id: '7',
    username: 'timm2345',
    message:
      '잔나비 목소리 너무 잘 어울려요. 잔나비에 다른 곡들도 함 불러보세요! 찰떡이실듯',
  },
  { id: '8', username: '지나2001', message: '잔나비보다는 한로로가 더 잘어울리는듯' },
  { id: '9', username: '나는야보컬왕', message: '최고' },
];
