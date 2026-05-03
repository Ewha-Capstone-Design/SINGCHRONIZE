'use client';

import { useState } from 'react';
import { useNavigate } from '@/shared/lib/navigation';
import { RECOMMEND_STEPS } from '@/shared/types/recommend';
import type { InternalRecommendStep } from '@/shared/types/recommend';
import type { SongUiType } from '@/entities/song/model/types';
import { saveRecordedAudio } from './useRecordedAudio';

import { isApiError } from '@/shared/api/apiError';
import { recommendationApi } from '@/entities/recommendation';

type FlowState = {
  jobId: string | null;
  audioBlob: Blob | null;
  firstSongs: SongUiType[];
  rankedSongIds: string[];
  selectedSituations: string[];
};

const INITIAL_STATE: FlowState = {
  jobId: null,
  audioBlob: null,
  firstSongs: [],
  rankedSongIds: [],
  selectedSituations: [],
};

// 추천 분석 플로우의 단계 전환
export const useRecommendFlow = () => {
  const { back, go, dynamic } = useNavigate();

  const [step, setStep] = useState<InternalRecommendStep>('record');
  const [flowState, setFlowState] = useState<FlowState>(INITIAL_STATE);

  const onRecordDone = (blob: Blob) => {
    setFlowState((prev) => ({ ...prev, audioBlob: blob }));
    setStep('analyze');
  };

  const goBack = () => {
    if (step === 'analyze') {
      setStep('record');
      return;
    }
    const currentIndex = RECOMMEND_STEPS.indexOf(step);
    if (currentIndex <= 0) {
      back();
      return;
    }
    const prevStep = RECOMMEND_STEPS[currentIndex - 1];
    if (prevStep) setStep(prevStep);
  };

  const onAnalyzeDone = (jobId: string, firstSongs: SongUiType[]) => {
    setFlowState((prev) => ({ ...prev, jobId, firstSongs }));
    setStep('ranking');
  };

  const onRankingDone = (rankedSongIds: string[]) => {
    setFlowState((prev) => ({ ...prev, rankedSongIds }));
    setStep('situation');
  };

  const onSituationDone = (selectedSituations: string[]) => {
    setFlowState((prev) => ({ ...prev, selectedSituations }));
    setStep('genre');
  };

  const onGenreDone = async (selectedGenres: string[]) => {
    const { jobId, rankedSongIds, selectedSituations, audioBlob } = flowState;
    if (!jobId) return;

    try {
      await recommendationApi.submitFeedback(jobId, {
        reranking_top3: rankedSongIds,
        selected_keyword: selectedSituations,
        selected_genre: selectedGenres,
      });
      if (audioBlob) saveRecordedAudio(jobId, audioBlob);
      go(dynamic.recommendResult(jobId));
    } catch (err) {
      if (isApiError(err)) {
        console.error(`[Recommend] 피드백 제출 실패 [${err.code}]:`, err.message, err);
      } else {
        console.error('[Recommend] 피드백 제출 실패:', err);
      }
    }
  };

  return {
    step,
    audioBlob: flowState.audioBlob,
    firstSongs: flowState.firstSongs,
    goBack,
    onRecordDone,
    onAnalyzeDone,
    onRankingDone,
    onSituationDone,
    onGenreDone,
  };
};
