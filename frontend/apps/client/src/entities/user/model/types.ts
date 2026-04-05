import type { components } from '@singchronize/api';
import type { AuthProvider } from '@/entities/auth';

export type UserUpdateRequest = components['schemas']['UserUpdateRequest'];
export type BlockSingerRequest = components['schemas']['BlockSingerRequest'];
export type BlockSongRequest = components['schemas']['BlockSongRequest'];
export type UserMeResponse = components['schemas']['UserMeResponse'];
export type UserResponse = components['schemas']['UserResponse'];

export interface FavoriteArtistUiType {
  id: number;
  name: string;
  imageUrl: string | null;
}

export interface UserUiType {
  id: string;
  nickname: string;
  email: string | null;
  profileImage: string | null;
  bio: string;
  provider: string;
  linkedProviders: string[];
  favoriteArtists: FavoriteArtistUiType[];
}

export interface SnsAccountUiType {
  provider: AuthProvider;
  connected: boolean;
  email?: string;
}

export const toUserUiType = (api: UserMeResponse): UserUiType => ({
  id: api.id,
  nickname: api.nickname,
  email: api.email ?? null,
  profileImage: api.profile_img ?? null,
  bio: api.bio ?? '',
  provider: api.provider,
  linkedProviders: api.linked_providers,
  favoriteArtists: (api.favorite_singers ?? []).map((singer) => ({
    id: singer.singer_id,
    name: singer.name,
    imageUrl: singer.photo_url ?? null,
  })),
});

export const toSnsAccountsUiType = (linkedProviders: string[]): SnsAccountUiType[] =>
  (['kakao', 'naver'] as const).map((provider) => ({
    provider,
    connected: linkedProviders.includes(provider),
  }));
