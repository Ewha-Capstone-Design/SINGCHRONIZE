'use client';

import { useEffect, useState } from 'react';
import SegmentedProgress from './SegmentedProgress';
import BackButton from './BackButton';

type FlowHeaderProps = {
  filled: number;
  onBack: () => void;
};

const FlowHeader = ({ filled, onBack }: FlowHeaderProps) => {
  const [animatedFilled, setAnimatedFilled] = useState(() => Math.max(0, filled - 1));

  useEffect(() => {
    setAnimatedFilled(Math.max(0, filled - 1));

    // 다음 프레임에 목표 값으로 변경
    const raf = requestAnimationFrame(() => {
      setAnimatedFilled(filled);
    });

    return () => cancelAnimationFrame(raf);
  }, [filled]);

  if (filled === 0) return null;

  return (
    <div className='pt-10 px-9 flex flex-col gap-10'>
      <SegmentedProgress filled={animatedFilled} />
      <BackButton onClick={onBack} />
    </div>
  );
};

export default FlowHeader;
