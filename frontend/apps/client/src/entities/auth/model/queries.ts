import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api/authApi';
import { tokenStore } from '@/shared/api/tokenStore';
import { queryKeys } from '@/shared/api/queryKeys';
import type { AuthProvider } from './types';

interface LoginVariables {
  provider: AuthProvider;
  accessToken: string;
  fcmToken?: string;
}

export const useLogin = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ provider, accessToken, fcmToken }: LoginVariables) =>
      authApi.login(provider, accessToken, fcmToken),
    onSuccess: (data) => {
      tokenStore.setAccess(data.access_token);
      tokenStore.setRefresh(data.refresh_token);
      queryClient.invalidateQueries({ queryKey: queryKeys.me });
    },
  });
};

export const useRefresh = () => {
  return useMutation({
    mutationFn: () => {
      const refreshToken = tokenStore.getRefresh();
      if (!refreshToken) throw new Error('리프레시 토큰이 없습니다.');
      return authApi.refresh(refreshToken);
    },
    onSuccess: (data) => {
      tokenStore.setAccess(data.access_token);
      tokenStore.setRefresh(data.refresh_token);
    },
    onError: () => {
      tokenStore.clear();
    },
  });
};

export const useWithdraw = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reason?: string) => authApi.withdraw(reason),
    onSuccess: () => {
      tokenStore.clear();
      queryClient.clear();
    },
  });
};
