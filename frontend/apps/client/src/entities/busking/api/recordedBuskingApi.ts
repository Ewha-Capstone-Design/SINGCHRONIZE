import { privateClient } from '@/shared/api/client';
import type { components } from '@singchronize/api';
import type { RecordedBuskingCreateBody } from '../model/types';

export const recordedBuskingApi = {
  // POST: 녹음 파일 S3 presigned URL 발급
  getRecordingUploadUrl: async (): Promise<
    components['schemas']['RecordingUploadUrlResponse']
  > => {
    const { data, error } = await privateClient.POST(
      '/api/v1/busking/recordings/upload-url',
      {},
    );
    if (error) throw error;
    return data;
  },

  // GET: 녹음 버스킹 목록 조회
  listRecordedBuskings: async (): Promise<
    components['schemas']['RecordedBuskingResponse'][]
  > => {
    const { data, error } = await privateClient.GET('/api/v1/busking/recordings');
    if (error) throw error;
    return data ?? [];
  },

  // POST: 녹음 버스킹 생성
  createRecordedBusking: async (
    body: RecordedBuskingCreateBody,
  ): Promise<components['schemas']['RecordedBuskingResponse']> => {
    const { data, error } = await privateClient.POST('/api/v1/busking/recordings', {
      body: body as unknown as components['schemas']['RecordedBuskingCreate'],
    });
    if (error) throw error;
    return data;
  },

  // GET: 녹음 버스킹 단건 조회
  getRecordedBusking: async (
    buskingId: string,
  ): Promise<components['schemas']['RecordedBuskingResponse']> => {
    const { data, error } = await privateClient.GET(
      '/api/v1/busking/recordings/{busking_id}',
      { params: { path: { busking_id: buskingId } } },
    );
    if (error) throw error;
    return data;
  },

  // POST: 썸네일 S3 presigned URL 발급
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
};

// S3 presigned URL로 파일 직접 업로드
export const uploadFileToS3 = async (
  uploadUrl: string,
  file: File,
  contentType: string,
): Promise<void> => {
  const res = await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': contentType },
  });
  if (!res.ok) throw new Error(`S3 업로드 실패 (${res.status})`);
};
