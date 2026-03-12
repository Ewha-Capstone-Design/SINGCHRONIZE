import type { ProfileUiType, SnsAccountUiType } from '@/entities/user/model/types';

export const MOCK_PROFILE: ProfileUiType = {
  nickname: '지연',
  profileImage: null,
  bio: '음악을 사랑하는 사람',
};

export const MOCK_SNS_ACCOUNTS: SnsAccountUiType[] = [
  { id: '1', provider: 'kakao', email: 'kimjiyeon1234@gmail.com', connected: true },
  { id: '2', provider: 'naver', connected: false },
];
