import { RecordingPhase } from '@/shared/types/recommend';

export const TITLE_BY_PHASE: Record<RecordingPhase, string> = {
  idle: '노래하는 목소리를 들려주세요!',
  recording: '노래를 계속 불러주세요.\n목소리를 듣고 있어요!',
  paused: '노래를 계속 불러주세요.\n목소리를 듣고 있어요!',
  enough: '충분히 들었어요!\n이제 멈춰도 괜찮아요.',
};

export const MAX_RECORD_SECONDS = 30;
