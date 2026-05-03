import { useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { buskingApi } from '../api/buskingApi';
import { queryKeys } from '@/shared/api/queryKeys';
import { toBuskingUi, toSetlistUi, toResultItemUi } from './mapper';
import type { BuskingRoomCreateBody } from './types';

// GET: 버스킹 방 목록 조회
export const useBuskingRooms = () =>
  useQuery({
    queryKey: queryKeys.buskingRooms,
    queryFn: buskingApi.getRooms,
    select: (data) => data.map((room) => toBuskingUi(room)),
  });

// GET: 버스킹 방 상세 조회
export const useBuskingRoom = (roomId: string) =>
  useQuery({
    queryKey: queryKeys.buskingRoom(roomId),
    queryFn: () => buskingApi.getRoom(roomId),
    enabled: !!roomId,
    select: (data) => ({
      ...data,
      setlist: data.setlist.map((item) => toSetlistUi(item, data.current_song_index)),
    }),
  });

// GET: 버스킹 결과 조회
export const useBuskingResult = (roomId: string) =>
  useQuery({
    queryKey: queryKeys.buskingResult(roomId),
    queryFn: () => buskingApi.getResult(roomId),
    enabled: !!roomId,
    select: (data) => ({
      ...data,
      setlist: data.setlist.map((item) => toResultItemUi(item, data.reactions)),
    }),
  });

// POST: 썸네일 presigned URL 발급
export const useGetThumbnailPresignedUrl = () =>
  useMutation({
    mutationFn: buskingApi.getThumbnailPresignedUrl,
  });

// POST: 버스킹 방 생성
export const useCreateBuskingRoom = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: BuskingRoomCreateBody) => buskingApi.createRoom(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.buskingRooms }),
  });
};

// POST: 버스킹 방 라이브 시작
export const useStartBuskingRoom = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roomId: string) => buskingApi.startRoom(roomId),
    onSuccess: (_data, roomId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.buskingRoom(roomId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.buskingRooms });
    },
  });
};

// POST: 버스킹 방 라이브 종료
export const useEndBuskingRoom = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roomId: string) => buskingApi.endRoom(roomId),
    onSuccess: (_data, roomId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.buskingRoom(roomId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.buskingRooms });
    },
  });
};

// POST: 버스킹 방 입장
export const useJoinBuskingRoom = () =>
  useMutation({
    mutationFn: (roomId: string) => buskingApi.joinRoom(roomId),
  });

// PATCH: 셋리스트 다음 곡으로 진행
export const useAdvanceSetlist = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roomId: string) => buskingApi.advanceSetlist(roomId),
    onSuccess: (_data, roomId) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.buskingRoom(roomId) }),
  });
};

// 버스킹 방 데이터 수동 무효화
export const useInvalidateBuskingRoom = () => {
  const queryClient = useQueryClient();
  return useCallback(
    (roomId: string) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.buskingRoom(roomId) }),
    [queryClient],
  );
};

// GET: 내 버스킹 기록 조회
export const useMyBuskingHistory = () =>
  useQuery({
    queryKey: queryKeys.myBuskingHistory,
    queryFn: buskingApi.getMyBuskingHistory,
  });
