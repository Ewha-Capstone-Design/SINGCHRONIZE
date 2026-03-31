import { publicClient, privateClient } from '@/shared/api/client';
import type {
  AuthProvider,
  LoginResponse,
  TokenResponse,
  SocialLoginRequest,
  WithdrawRequest,
} from '../model/types';

export const authApi = {
  login: async (
    provider: AuthProvider,
    credential: string,
    fcmToken?: string,
  ): Promise<LoginResponse> => {
    const body: SocialLoginRequest = {
      access_token: credential,
      fcm_token: fcmToken,
    };

    const { data, error } = await publicClient.POST('/api/v1/auth/login/{provider}', {
      params: { path: { provider } },
      body,
    });

    if (error) throw error;
    if (!data) throw new Error('로그인 응답 데이터가 없습니다.');

    return data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const { data, error } = await publicClient.POST('/api/v1/auth/refresh', {
      headers: { Authorization: `Bearer ${refreshToken}` },
    });

    if (error) throw error;
    if (!data) throw new Error('토큰 재발급 응답 데이터가 없습니다.');

    return data;
  },

  withdraw: async (reason?: string): Promise<void> => {
    const body: WithdrawRequest = {
      reason,
    };

    const { error } = await privateClient.POST('/api/v1/auth/withdraw', {
      body,
    });

    if (error) throw error;
  },
};
