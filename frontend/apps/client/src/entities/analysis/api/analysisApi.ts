import { privateClient } from '@/shared/api/client';
import type { components } from '@singchronize/api';

export const analysisApi = {
  // POST: presigned URL 발급
  getUploadUrl: async (): Promise<components['schemas']['UploadUrlResponse']> => {
    const { data, error } = await privateClient.POST('/api/v1/analysis/upload-url', {});
    if (error) throw error;
    return data;
  },

  // POST: 분석 Job 생성 (S3 업로드 완료 후 호출)
  createJob: async (
    body: components['schemas']['AnalysisJobCreate'],
  ): Promise<components['schemas']['AnalysisJobResponse']> => {
    const { data, error } = await privateClient.POST('/api/v1/analysis/jobs', { body });
    if (error) throw error;
    return data;
  },

  // GET: 분석 Job 상태 조회
  getJob: async (
    jobId: string,
  ): Promise<components['schemas']['AnalysisJobResponse']> => {
    const { data, error } = await privateClient.GET('/api/v1/analysis/jobs/{job_id}', {
      params: { path: { job_id: jobId } },
    });
    if (error) throw error;
    return data;
  },

  // GET: 보컬 프로필 조회
  getVocalProfile: async (): Promise<components['schemas']['VocalProfileResponse']> => {
    const { data, error } = await privateClient.GET('/api/v1/analysis/profile');
    if (error) throw error;
    return data;
  },
};
