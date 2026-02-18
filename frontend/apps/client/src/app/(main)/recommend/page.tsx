'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { FlowHeader, StepAnalyze } from './_components';
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

  const bgClass =
    step === 'record'
      ? 'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.20)_0%,rgba(22,22,22,0.20)_100%)] bg-size-[100%_150%] bg-position-[50%_-30%]'
      : 'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.30)_0%,rgba(22,22,22,0.30)_100%)] bg-size-[150%_170%] bg-position-[50%_-20%]';

  return (
    <div
      className={`
      flex flex-col w-full h-screen text-white overflow-hidden
      bg-bg bg-no-repeat transition-[background-position] duration-700 ease-out
      ${bgClass}`}
    >
      <FlowHeader step={step} onBack={handleBack} />
      <div className='flex-1 flex flex-col items-center'>
        {step === 'record' && <StepRecord onNext={() => setStep('analyze')} />}
        {step === 'analyze' && <StepAnalyze onNext={() => setStep('ranking')} />}
        {step === 'ranking' && <StepRanking onNext={() => setStep('keyword')} />}
      </div>
    </div>
  );
};

export default RecommendPage;
