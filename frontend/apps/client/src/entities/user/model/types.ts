export interface ProfileApiType {
  nickname: string;
  profile_img: string;
  bio?: string;
}

export interface ProfileUiType {
  nickname: string;
  profileImage: string | null;
  bio: string;
}

export const toProfileUiType = (api: ProfileApiType): ProfileUiType => ({
  nickname: api.nickname,
  profileImage: api.profile_img ?? null,
  bio: api.bio ?? '',
});

export interface SnsAccountUiType {
  id: string;
  provider: 'kakao' | 'naver';
  email?: string;
  connected: boolean;
}
