'use client';

import { useEffect, useState } from 'react';

type AnalyzeStatus = 'uploading' | 'analyzing' | 'searching' | 'done';

const ANALYZE_TEXT_BY_STATUS: Record<AnalyzeStatus, { title: string; desc: string }> = {
  uploading: {
    title: '분석을 시작할게요!',
    desc: '음성을 업로드하고 있어요.',
  },
  analyzing: {
    title: '조금만 기다려주세요!',
    desc: '목소리를 분석하고 있어요.',
  },
  searching: {
    title: '이제 거의 다 왔어요!',
    desc: '잘 어울리는 노래를 찾고 있어요.',
  },
  done: {
    title: '준비가 끝났어요!',
    desc: '당신에게 딱 맞는 노래를 찾았어요!',
  },
};

// 각 단계별 분석 시간(ms), TODO: 추후 서버 이벤트로 수정
const STATUS_ORDER: AnalyzeStatus[] = ['uploading', 'analyzing', 'searching', 'done'];

const STATUS_DURATION: Record<AnalyzeStatus, number> = {
  uploading: 1200,
  analyzing: 1600,
  searching: 1600,
  done: 800,
};

type StepAnalyzeProps = {
  onNext: () => void;
};

const StepAnalyze = ({ onNext }: StepAnalyzeProps) => {
  const [status, setStatus] = useState<AnalyzeStatus>('uploading');

  useEffect(() => {
    const duration = STATUS_DURATION[status];

    const t = setTimeout(() => {
      if (status === 'done') {
        onNext();
        return;
      }

      const idx = STATUS_ORDER.indexOf(status);
      const next = STATUS_ORDER[idx + 1];
      if (next) {
        setStatus(next);
      }
    }, duration);

    return () => clearTimeout(t);
  }, [status, onNext]);

  const text = ANALYZE_TEXT_BY_STATUS[status];

  return (
    <div className='flex-1 w-full flex items-center justify-center'>
      <div className='flex flex-col items-center typo-32b text-center'>
        <p>{text.title}</p>
        <p>{text.desc}</p>
      </div>
    </div>
  );
};

export default StepAnalyze;
