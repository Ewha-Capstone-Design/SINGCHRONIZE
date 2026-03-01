export type RecordingVariant = 'start' | 'pause' | 'done';

export type RecordingPhase = 'idle' | 'recording' | 'paused' | 'finish';

export const RECOMMEND_STEPS = [
  'record',
  'ranking',
  'situation',
  'genre',
  'result',
] as const;

export type RecommendStep = (typeof RECOMMEND_STEPS)[number];

export type InternalRecommendStep = RecommendStep | 'analyze';

export const FILLED_COUNT_BY_STEP: Record<RecommendStep, number> = {
  record: 1,
  ranking: 2,
  situation: 3,
  genre: 3,
  result: 4,
};
