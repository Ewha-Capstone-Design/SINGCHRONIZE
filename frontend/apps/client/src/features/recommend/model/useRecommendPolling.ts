'use client';

import { useEffect, useRef, useState } from 'react';
import type { SongUiType } from '@/entities/song/model/types';
import { toFirstRecommendedSongUi } from '@/entities/song/model/mapper';

import { isApiError } from '@/shared/api/apiError';
import { analysisApi } from '@/entities/analysis';
import { recommendationApi } from '@/entities/recommendation';

export type AnalyzeStatus = 'uploading' | 'analyzing' | 'searching' | 'done' | 'error';

type OnDone = (jobId: string, firstSongs: SongUiType[]) => void;

const POLL_INTERVAL_MS = 3000;
const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

// 보컬 분석 → 추천 Job 생성 → WAITING_FEEDBACK까지 풀 파이프라인 실행
// uploading → analyzing → searching → done 순서로 status 전환
export const useRecommendPolling = (audioBlob: Blob, onDone: OnDone) => {
  const [status, setStatus] = useState<AnalyzeStatus>('uploading');
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  useEffect(() => {
    let cancelled = false;

    const pollAnalysis = async (jobId: string): Promise<void> => {
      if (cancelled) return;
      const result = await analysisApi.getJob(jobId);
      if (cancelled) return;

      if (result.status === 'DONE') return;
      if (result.status === 'FAILED') {
        console.error('[Analysis] Job FAILED:', result);
        throw new Error(result.error_message ?? '보컬 분석에 실패했습니다.');
      }
      await delay(POLL_INTERVAL_MS);
      await pollAnalysis(jobId);
    };

    const pollRecommendation = async (jobId: string): Promise<void> => {
      if (cancelled) return;
      const result = await recommendationApi.getStatus(jobId);
      if (cancelled) return;

      if (result.status === 'WAITING_FEEDBACK' || result.status === 'DONE') {
        await delay(600);
        if (cancelled) return;
        setStatus('done');
        await delay(800);
        if (cancelled) return;
        const firstSongs = (result.first_recommended_songs ?? []).map(
          toFirstRecommendedSongUi,
        );
        onDoneRef.current(result.job_id, firstSongs);
        return;
      }
      if (result.status === 'FAILED') {
        console.error('[Recommend] Job FAILED:', result);
        throw new Error('추천 생성에 실패했습니다.');
      }
      await delay(POLL_INTERVAL_MS);
      await pollRecommendation(jobId);
    };

    const run = async () => {
      try {
        // 1. presigned URL 발급 → S3 업로드
        setStatus('uploading');
        const { upload_url, s3_key } = await analysisApi.getUploadUrl();
        if (cancelled) return;

        console.log('[Analysis] S3 upload 시작:', {
          s3_key,
          blobType: audioBlob.type,
          blobSize: audioBlob.size,
        });
        const uploadRes = await fetch(upload_url, {
          method: 'PUT',
          headers: { 'Content-Type': 'audio/m4a' },
          body: audioBlob,
        });
        if (!uploadRes.ok) {
          console.error(
            '[Analysis] S3 upload 실패:',
            uploadRes.status,
            uploadRes.statusText,
          );
          throw new Error(`S3 업로드 실패 (${uploadRes.status})`);
        }
        if (cancelled) return;

        // 2. 분석 Job 생성 → DONE까지 폴링
        setStatus('analyzing');
        const analysisJob = await analysisApi.createJob({ s3_key });
        if (cancelled) return;

        await pollAnalysis(analysisJob.job_id);
        if (cancelled) return;

        // 3. 추천 Job 생성 → WAITING_FEEDBACK까지 폴링
        setStatus('searching');
        const recommendJob = await recommendationApi.create({
          base_report_id: analysisJob.job_id,
        });
        if (cancelled) return;

        await pollRecommendation(recommendJob.job_id);
      } catch (err) {
        if (isApiError(err)) {
          console.error(`[Recommend] API error [${err.code}]:`, err.message, err);
        } else {
          console.error('[Recommend] Unexpected error:', err);
        }
        setStatus('error');
      }
    };

    run();

    return () => {
      cancelled = true;
    };
  }, [audioBlob]);

  return { status };
};
