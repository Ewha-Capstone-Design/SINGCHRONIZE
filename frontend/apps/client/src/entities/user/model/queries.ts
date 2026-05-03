import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../api/userApi';
import { queryKeys } from '@/shared/api/queryKeys';
import { toUserUiType } from './types';

// GET: 사용자 정보
export const useMe = () =>
  useQuery({
    queryKey: queryKeys.me,
    queryFn: userApi.getMe,
    select: toUserUiType,
    staleTime: 5 * 60 * 1000,
  });

// PATCH: 닉네임 수정
export const useUpdateMe = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.updateMe,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.me }),
  });
};

// PATCH: 프로필 수정
export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.updateProfile,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.me }),
  });
};

// DELETE: SNS 연동 해제
export const useUnlinkAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.unlinkAccount,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.me }),
  });
};

// GET: 차단한 가수 목록
export const useBlockedSingers = () =>
  useQuery({
    queryKey: queryKeys.blockedSingers,
    queryFn: userApi.getBlockedSingers,
  });

// POST: 가수 차단하기
export const useBlockSinger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.blockSinger,
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.blockedSingers }),
  });
};

// DELETE: 가수 차단 해제하기
export const useUnblockSinger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.unblockSinger,
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.blockedSingers }),
  });
};

// GET: 차단한 곡 목록
export const useBlockedSongs = () =>
  useQuery({
    queryKey: queryKeys.blockedSongs,
    queryFn: userApi.getBlockedSongs,
  });

// POST: 곡 차단하기
export const useBlockSong = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.blockSong,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.blockedSongs }),
  });
};

// DELETE: 곡 차단 해제하기
export const useUnblockSong = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.unblockSong,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.blockedSongs }),
  });
};

// POST: 온보딩 1단계
export const useOnboardingStep1 = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.onboardingStep1,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.me }),
  });
};

// POST: 온보딩 2단계
export const useOnboardingStep2 = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.onboardingStep2,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.me }),
  });
};
