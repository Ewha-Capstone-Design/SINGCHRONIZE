import { publicClient, privateClient } from '@/shared/api/client';
import type { AuthProvider, LoginResponse, TokenResponse } from '../model/types';

export const authApi = {
  login: async (
    provider: AuthProvider,
    accessToken: string,
    fcmToken?: string,
  ): Promise<LoginResponse> => {
    const { data, error } = await publicClient.POST('/api/v1/auth/login/{provider}', {
      params: { path: { provider } },
      body: { access_token: accessToken, fcm_token: fcmToken },
    });
    if (error) throw error;
    return data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const { data, error } = await publicClient.POST('/api/v1/auth/refresh', {
      headers: { Authorization: `Bearer ${refreshToken}` },
    });
    if (error) throw error;
    return data;
  },

  withdraw: async (reason?: string): Promise<void> => {
    const { error } = await privateClient.POST('/api/v1/auth/withdraw', {
      body: { reason },
    });
    if (error) throw error;
  },
};
