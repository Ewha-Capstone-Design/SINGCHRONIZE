import { privateClient } from '@/shared/api/client';
import type { AuthProvider } from '@/entities/auth';
import type {
  UserUpdateRequest,
  SettingsUpdateRequest,
  BlockSingerRequest,
  BlockSongRequest,
} from '../model/types';

export const userApi = {
  // GET: 사용자 정보
  getMe: async () => {
    const { data, error } = await privateClient.GET('/api/v1/users/me');
    if (error) throw error;
    return data;
  },

  // PATCH: 닉네임 수정
  updateMe: async (body: UserUpdateRequest) => {
    const { data, error } = await privateClient.PATCH('/api/v1/users/me', { body });
    if (error) throw error;
    return data;
  },

  // PATCH: 프로필 수정
  updateProfile: async (formData: FormData) => {
    const { data, error } = await privateClient.PATCH('/api/v1/users/me/profile', {
      body: formData as never,
    });
    if (error) throw error;
    return data;
  },

  // DELETE: SNS 연동 해제
  unlinkAccount: async (provider: AuthProvider) => {
    const { error } = await privateClient.DELETE(
      '/api/v1/users/me/linked-accounts/{provider}',
      {
        params: { path: { provider } },
      },
    );
    if (error) throw error;
  },

  // GET: 차단한 가수 목록
  getBlockedSingers: async () => {
    const { data, error } = await privateClient.GET('/api/v1/users/me/blocked-singers');
    if (error) throw error;
    return data;
  },

  // POST: 가수 차단하기
  blockSinger: async (body: BlockSingerRequest) => {
    const { data, error } = await privateClient.POST('/api/v1/users/me/blocked-singers', {
      body,
    });
    if (error) throw error;
    return data;
  },

  // DELETE: 가수 차단 해제하기
  unblockSinger: async (singerId: number) => {
    const { error } = await privateClient.DELETE(
      '/api/v1/users/me/blocked-singers/{singer_id}',
      { params: { path: { singer_id: singerId } } },
    );
    if (error) throw error;
  },

  // GET: 차단한 곡 목록
  getBlockedSongs: async () => {
    const { data, error } = await privateClient.GET('/api/v1/users/me/blocked-songs');
    if (error) throw error;
    return data;
  },

  // POST: 곡 차단하기
  blockSong: async (body: BlockSongRequest) => {
    const { data, error } = await privateClient.POST('/api/v1/users/me/blocked-songs', {
      body,
    });
    if (error) throw error;
    return data;
  },

  // DELETE: 곡 차단 해제하기
  unblockSong: async (songId: string) => {
    const { error } = await privateClient.DELETE(
      '/api/v1/users/me/blocked-songs/{song_id}',
      { params: { path: { song_id: songId } } },
    );
    if (error) throw error;
  },

  // POST: 닉네임/프로필 사진 등록 (온보딩 1단계)
  onboardingStep1: async (formData: FormData) => {
    const { data, error } = await privateClient.POST(
      '/api/v1/users/me/onboarding/step1',
      {
        body: formData as never,
      },
    );
    if (error) throw error;
    return data;
  },

  // POST: 즐겨부르는 가수 선택 (온보딩 2단계)
  onboardingStep2: async (singerIds: number[]) => {
    const { data, error } = await privateClient.POST(
      '/api/v1/users/me/onboarding/step2',
      {
        body: { singer_ids: singerIds },
      },
    );
    if (error) throw error;
    return data;
  },
};
