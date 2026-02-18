// 보컬 녹음
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

// 마이크 테스트
export type LevelStatus = 'high' | 'low' | 'ok';

export const MIC_TEST_TEXT_BY_STATE = {
  beforeTest: {
    title: '마이크 테스트 먼저 해볼까요?',
    subtitle: '시작하기를 눌러 진행해 주세요!',
  },
  testing: {
    high: {
      title: '소리가 크게 들려요',
      subtitle: '볼륨을 조금 낮춰 주세요!',
    },
    low: {
      title: '소리가 작게 들려요',
      subtitle: '볼륨을 조금 높여 주세요!',
    },
    ok: {
      title: '소리가 적절하게 들려요',
      subtitle: '지금 상태를 유지해 주세요!',
    },
  },
} as const;
