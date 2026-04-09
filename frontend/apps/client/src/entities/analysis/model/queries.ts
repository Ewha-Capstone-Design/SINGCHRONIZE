import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analysisApi } from '../api/analysisApi';
import { queryKeys } from '@/shared/api/queryKeys';
import { adaptVocalReport } from '@/entities/vocal-report';

// POST: presigned URL 발급
export const useGetAnalysisUploadUrl = () =>
  useMutation({
    mutationFn: analysisApi.getUploadUrl,
  });

// POST: 분석 Job 생성
export const useCreateAnalysisJob = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: analysisApi.createJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.vocalProfile });
    },
  });
};

// GET: 분석 Job 상태 조회
export const useAnalysisJob = (jobId: string) =>
  useQuery({
    queryKey: queryKeys.analysisJob(jobId),
    queryFn: () => analysisApi.getJob(jobId),
    enabled: !!jobId,
  });

// GET: 보컬 프로필 조회
export const useVocalProfile = () =>
  useQuery({
    queryKey: queryKeys.vocalProfile,
    queryFn: analysisApi.getVocalProfile,
    select: adaptVocalReport,
  });
