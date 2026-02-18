import { useEffect, useState } from 'react';
import SegmentedProgress from './SegmentedProgress';
import { IcBack } from '@/shared/assets/icons';
import { RecommendStep, FILLED_COUNT_BY_STEP } from '@/shared/types/recommend';

type FlowHeaderProps = {
  step: RecommendStep;
  onBack: () => void;
};

const FlowHeader = ({ step, onBack }: FlowHeaderProps) => {
  if (step === 'analyze') return null;

  const targetFilled = FILLED_COUNT_BY_STEP[step];

  const [animatedFilled, setAnimatedFilled] = useState<number>(() =>
    Math.max(0, targetFilled - 1)
  );

  useEffect(() => {
    setAnimatedFilled(Math.max(0, targetFilled - 1));

    // 다음 프레임에 목표 값으로 변경
    const raf = requestAnimationFrame(() => {
      setAnimatedFilled(targetFilled);
    });

    return () => cancelAnimationFrame(raf);
  }, [targetFilled]);

  return (
    <div className='pt-10 px-9 flex flex-col gap-10'>
      <SegmentedProgress filled={animatedFilled} />
      <IcBack onClick={onBack} />
    </div>
  );
};

export default FlowHeader;
