import { privateClient } from '@/shared/api/client';
import type { components } from '@singchronize/api';
import type { BuskingResultApiType } from '../model/types';

export const buskingApi = {
  // POST: 썸네일 업로드용 presigned URL 발급
  getThumbnailPresignedUrl: async (): Promise<
    components['schemas']['ThumbnailPresignedResponse']
  > => {
    const { data, error } = await privateClient.POST(
      '/api/v1/busking/thumbnail/presigned-url',
      {},
    );
    if (error) throw error;
    return data;
  },

  // GET: 버스킹 방 목록 조회
  getRooms: async (): Promise<components['schemas']['BuskingRoomResponse'][]> => {
    const { data, error } = await privateClient.GET('/api/v1/busking/rooms');
    if (error) throw error;
    return data ?? [];
  },

  // POST: 버스킹 방 생성 (LiveKit 호스트 토큰 포함)
  createRoom: async (
    body: components['schemas']['BuskingRoomCreate'],
  ): Promise<components['schemas']['BuskingRoomCreateResponse']> => {
    const { data, error } = await privateClient.POST('/api/v1/busking/rooms', { body });
    if (error) throw error;
    return data;
  },

  // GET: 버스킹 방 상세 조회
  getRoom: async (
    roomId: string,
  ): Promise<components['schemas']['BuskingRoomDetailResponse']> => {
    const { data, error } = await privateClient.GET('/api/v1/busking/rooms/{room_id}', {
      params: { path: { room_id: roomId } },
    });
    if (error) throw error;
    return data;
  },

  // POST: 버스킹 방 라이브 시작
  startRoom: async (
    roomId: string,
  ): Promise<components['schemas']['BuskingRoomResponse']> => {
    const { data, error } = await privateClient.POST(
      '/api/v1/busking/rooms/{room_id}/start',
      { params: { path: { room_id: roomId } } },
    );
    if (error) throw error;
    return data;
  },

  // POST: 버스킹 방 라이브 종료
  endRoom: async (
    roomId: string,
  ): Promise<components['schemas']['BuskingRoomResponse']> => {
    const { data, error } = await privateClient.POST(
      '/api/v1/busking/rooms/{room_id}/end',
      { params: { path: { room_id: roomId } } },
    );
    if (error) throw error;
    return data;
  },

  // POST: 버스킹 방 입장 (LiveKit 뷰어 토큰 발급)
  joinRoom: async (
    roomId: string,
  ): Promise<components['schemas']['LiveKitJoinResponse']> => {
    const { data, error } = await privateClient.POST(
      '/api/v1/busking/rooms/{room_id}/join',
      { params: { path: { room_id: roomId } } },
    );
    if (error) throw error;
    return data;
  },

  // PATCH: 셋리스트 다음 곡으로 진행
  advanceSetlist: async (
    roomId: string,
  ): Promise<components['schemas']['BuskingRoomResponse']> => {
    const { data, error } = await privateClient.PATCH(
      '/api/v1/busking/rooms/{room_id}/setlist/current',
      { params: { path: { room_id: roomId } } },
    );
    if (error) throw error;
    return data;
  },

  // GET: 버스킹 결과 조회
  getResult: async (
    roomId: string,
  ): Promise<BuskingResultApiType> => {
    const { data, error } = await privateClient.GET(
      '/api/v1/busking/rooms/{room_id}/result',
      { params: { path: { room_id: roomId } } },
    );
    if (error) throw error;
    return data;
  },

  // GET: 내 버스킹 기록 조회
  getMyBuskingHistory: async (): Promise<
    components['schemas']['_BuskingHistoryResponse']
  > => {
    const { data, error } = await privateClient.GET('/api/v1/users/me/busking-history');
    if (error) throw error;
    return data;
  },
};
