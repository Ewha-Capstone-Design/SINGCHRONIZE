'use client';

import { useRecommendPolling } from '../model/useRecommendPolling';
import type { AnalyzeStatus } from '../model/useRecommendPolling';
import type { SongUiType } from '@/entities/song/model/types';

const STATUS_TEXT: Record<AnalyzeStatus, { title: string; desc: string }> = {
  uploading: { title: '분석을 시작할게요!', desc: '음성을 업로드하고 있어요.' },
  analyzing: { title: '조금만 기다려주세요!', desc: '목소리를 분석하고 있어요.' },
  searching: { title: '이제 거의 다 왔어요!', desc: '잘 어울리는 노래를 찾고 있어요.' },
  done: { title: '준비가 끝났어요!', desc: '당신에게 딱 맞는 노래를 찾았어요!' },
  error: { title: '오류가 발생했어요.', desc: '잠시 후 다시 시도해 주세요.' },
};

type StepAnalyzeProps = {
  audioBlob: Blob;
  onNext: (jobId: string, firstSongs: SongUiType[]) => void;
};

const StepAnalyze = ({ audioBlob, onNext }: StepAnalyzeProps) => {
  const { status } = useRecommendPolling(audioBlob, onNext);
  const text = STATUS_TEXT[status];

  return (
    <div className='pb-29 flex-1 w-full flex items-center justify-center'>
      <div className='flex flex-col items-center typo-32b text-center'>
        <p>{text.title}</p>
        <p>{text.desc}</p>
      </div>
    </div>
  );
};

export default StepAnalyze;
