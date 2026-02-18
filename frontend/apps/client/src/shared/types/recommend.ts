export type RecordingVariant = 'start' | 'pause' | 'done';

export type RecordingPhase = 'idle' | 'recording' | 'paused' | 'finish';

export type RecommendStep = 'record' | 'analyze' | 'ranking' | 'keyword' | 'result';

export type ProgressStep = Exclude<RecommendStep, 'analyze'>;

export const RECOMMEND_STEPS: RecommendStep[] = [
  'record',
  'ranking',
  'keyword',
  'result',
];

export const FILLED_COUNT_BY_STEP: Record<ProgressStep, number> = {
  record: 1,
  ranking: 2,
  keyword: 3,
  result: 4,
};
