export const MAX_RECORD_SECONDS = 60;

export const RECORD_GUIDE_THRESHOLDS = {
  ENOUGH: 35,
  WARNING: 50,
  FORCE_END: 60,
} as const;

export type RecordGuideLevel = 'default' | 'enough' | 'warning';

export const GUIDE_TEXT_BY_LEVEL: Record<RecordGuideLevel, string> = {
  default: '노래를 계속 불러주세요\n목소리를 듣고 있어요!',
  enough: '충분히 들었어요!\n이제 멈춰도 괜찮아요',
  warning: '녹음이 곧 종료돼요!\n이제 멈춰도 괜찮아요',
};
