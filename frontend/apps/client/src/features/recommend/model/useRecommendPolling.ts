'use client';

import { useEffect, useRef, useState } from 'react';
import { recommendationApi } from '@/entities/recommendation';
import { toSongUi } from '@/entities/song/model/mapper';
import type { SongUiType } from '@/entities/song/model/types';

export type AnalyzeStatus = 'uploading' | 'analyzing' | 'searching' | 'done' | 'error';

type OnDone = (jobId: string, firstSongs: SongUiType[]) => void;

const POLL_INTERVAL_MS = 3000;
const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

// 추천 Job을 생성하고 WAITING_FEEDBACK 상태까지 폴링
// 완료 시 onDone으로 jobId와 1차 추천곡을 전달
export const useRecommendPolling = (onDone: OnDone) => {
  const [status, setStatus] = useState<AnalyzeStatus>('uploading');
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  useEffect(() => {
    let cancelled = false;

    const poll = async (jobId: string): Promise<void> => {
      if (cancelled) return;

      const result = await recommendationApi.getStatus(jobId);
      if (cancelled) return;

      if (result.status === 'WAITING_FEEDBACK' || result.status === 'DONE') {
        setStatus('searching');
        await delay(600);
        if (cancelled) return;

        setStatus('done');
        await delay(800);
        if (cancelled) return;

        const firstSongs = (result.first_recommended_songs ?? []).map(toSongUi);
        onDoneRef.current(result.job_id, firstSongs);
      } else if (result.status === 'FAILED') {
        setStatus('error');
      } else {
        await delay(POLL_INTERVAL_MS);
        await poll(jobId);
      }
    };

    const run = async () => {
      try {
        setStatus('uploading');
        const job = await recommendationApi.create();
        if (cancelled) return;

        setStatus('analyzing');
        await poll(job.job_id);
      } catch {
        setStatus('error');
      }
    };

    run();

    return () => {
      cancelled = true;
    };
  }, []);

  return { status };
};
