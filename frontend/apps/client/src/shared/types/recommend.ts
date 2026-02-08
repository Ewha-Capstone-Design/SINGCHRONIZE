export type RecordingVariant = 'start' | 'pause' | 'done';

export type RecordingPhase = 'idle' | 'recording' | 'paused' | 'enough';

export type RecommendStep = 'record' | 'ranking' | 'keyword' | 'result';

export const RECOMMEND_STEPS: RecommendStep[] = [
  'record',
  'ranking',
  'keyword',
  'result',
];

export const FILLED_COUNT_BY_STEP: Record<RecommendStep, number> = {
  record: 1,
  ranking: 2,
  keyword: 3,
  result: 4,
};
