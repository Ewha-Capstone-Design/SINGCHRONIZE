'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { FlowHeader } from './_components';
import { StepRecord } from '@/features/record';
import { StepRanking } from '@/features/ranking';
import { RecommendStep, RECOMMEND_STEPS } from '@/shared/types/recommend';

const RecommendPage = () => {
  const router = useRouter();

  const [step, setStep] = useState<RecommendStep>('record');

  const handleBack = () => {
    const currentIndex = RECOMMEND_STEPS.indexOf(step);

    if (currentIndex <= 0) {
      router.back();
      return;
    }

    const prevStep = RECOMMEND_STEPS[currentIndex - 1];
    if (!prevStep) return;
    setStep(prevStep);
  };

  return (
    <div
      className='
      w-full h-screen text-white overflow-hidden
      flex flex-col
      bg-bg
      bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.20)_0%,rgba(22,22,22,0.20)_100%)]
      bg-no-repeat
      bg-size-[100%_140%]
      bg-position-[50%_-70%]'
    >
      <FlowHeader step={step} onBack={handleBack} />
      <div className='flex-1 flex flex-col items-center'>
        {step === 'record' && <StepRecord onNext={() => setStep('ranking')} />}
        {step === 'ranking' && <StepRanking onNext={() => setStep('keyword')} />}
      </div>
    </div>
  );
};

export default RecommendPage;
