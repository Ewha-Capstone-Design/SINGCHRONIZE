'use client';

import { FlowHeader } from '@/shared/components';
import { StepRecord } from '@/features/record';
import { StepRanking } from '@/features/ranking';
import { StepAnalyze, StepSituation, StepGenre } from '@/features/recommend/ui';
import { useRecommendFlow } from '@/features/recommend/model';
import { FILLED_COUNT_BY_STEP } from '@/shared/types/recommend';

const BG_CLASS = {
  record:
    'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.20)_0%,rgba(22,22,22,0.20)_100%)] bg-size-[100%_150%] bg-position-[50%_-30%]',
  other:
    'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.30)_0%,rgba(22,22,22,0.30)_100%)] bg-size-[150%_170%] bg-position-[50%_-20%]',
} as const;

const RecommendAnalyzePage = () => {
  const {
    step,
    firstSongs,
    goBack,
    onRecordDone,
    onAnalyzeDone,
    onRankingDone,
    onSituationDone,
    onGenreDone,
  } = useRecommendFlow();

  const filled = FILLED_COUNT_BY_STEP[step];

  return (
    <div
      className={`
        flex flex-col w-full h-screen text-white overflow-hidden
        bg-bg bg-no-repeat transition-[background-position] duration-700 ease-out
        ${step === 'record' ? BG_CLASS.record : BG_CLASS.other}
      `}
    >
      <FlowHeader filled={filled} onBack={goBack} />
      <div className='flex-1 flex flex-col items-center'>
        {step === 'record' && <StepRecord onNext={onRecordDone} />}
        {step === 'analyze' && <StepAnalyze onNext={onAnalyzeDone} />}
        {step === 'ranking' && <StepRanking songs={firstSongs} onNext={onRankingDone} />}
        {step === 'situation' && <StepSituation onNext={onSituationDone} />}
        {step === 'genre' && <StepGenre onNext={onGenreDone} />}
      </div>
    </div>
  );
};

export default RecommendAnalyzePage;
