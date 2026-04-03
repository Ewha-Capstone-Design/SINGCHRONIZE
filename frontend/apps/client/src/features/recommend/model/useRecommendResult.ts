'use client';

import { useEffect, useRef, useState } from 'react';
import { recommendationApi } from '@/entities/recommendation';
import { buildRecommendTabs } from './mapper';
import type { SongApiType } from '@/entities/song';
import type { RecommendSongType, RecommendTab } from '@/widgets/vocal-analyze/model';

const POLL_INTERVAL_MS = 3000;
const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

// 추천 결과가 DONE 상태가 될 때까지 폴링하고 탭 데이터를 반환
export const useRecommendResult = (jobId: string | null) => {
  const [isLoading, setIsLoading] = useState(!!jobId);
  const [situationTabs, setSituationTabs] = useState<RecommendTab<RecommendSongType>[]>(
    [],
  );
  const [genreTabs, setGenreTabs] = useState<RecommendTab<RecommendSongType>[]>([]);
  const cancelledRef = useRef(false);

  useEffect(() => {
    if (!jobId) return;
    cancelledRef.current = false;

    const poll = async (): Promise<void> => {
      if (cancelledRef.current) return;

      const result = await recommendationApi.getStatus(jobId);
      if (cancelledRef.current) return;

      if (result.status === 'DONE') {
        const { situationTabs, genreTabs } = buildRecommendTabs(
          (result.recommended_songs ?? {}) as Record<string, SongApiType[]>,
        );
        setSituationTabs(situationTabs);
        setGenreTabs(genreTabs);
        setIsLoading(false);
      } else if (result.status === 'FAILED') {
        setIsLoading(false);
      } else {
        await delay(POLL_INTERVAL_MS);
        await poll();
      }
    };

    poll().catch(() => {
      if (!cancelledRef.current) setIsLoading(false);
    });

    return () => {
      cancelledRef.current = true;
    };
  }, [jobId]);

  return { isLoading, situationTabs, genreTabs };
};
