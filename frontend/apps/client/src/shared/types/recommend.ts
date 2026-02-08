export type RecordingVariant = 'start' | 'pause' | 'done';

export type RecordingPhase = 'idle' | 'recording' | 'paused' | 'enough';

export type RecommendStep = 'record' | 'analyzing' | 'rank' | 'keyword' | 'result';

export const RECOMMEND_STEPS: RecommendStep[] = [
  'record',
  'analyzing',
  'rank',
  'keyword',
  'result',
];

export const FILLED_COUNT_BY_STEP: Record<RecommendStep, number> = {
  record: 1,
  analyzing: 2,
  rank: 3,
  keyword: 4,
  result: 4,
};
