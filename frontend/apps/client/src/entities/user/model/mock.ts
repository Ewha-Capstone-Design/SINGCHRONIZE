import type { UserUiType, SnsAccountUiType } from '@/entities/user/model/types';

export const MOCK_PROFILE: UserUiType = {
  id: 'mock-id',
  nickname: '지연',
  email: null,
  profileImage: null,
  bio: '음악을 사랑하는 사람',
  provider: 'kakao',
  linkedProviders: ['kakao'],
};

export const MOCK_SNS_ACCOUNTS: SnsAccountUiType[] = [
  { provider: 'kakao', connected: true },
  { provider: 'naver', connected: false },
];
