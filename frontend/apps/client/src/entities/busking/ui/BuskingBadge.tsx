'use client';

import { cn } from '@/shared/lib/cn';

type BuskingBadgeProps = {
  isRecord: boolean;
  duration: string;
  className?: string;
};

const BuskingBadge = ({ isRecord, duration, className }: BuskingBadgeProps) => {
  return (
    <div
      className={cn(
        'px-3 py-1 flex gap-1 rounded-10 typo-16m',
        isRecord ? 'bg-brand text-black' : 'bg-accent-600 text-white',
        className
      )}
    >
      <span>{isRecord ? 'Record' : 'LIVE'}</span>
      <span>·</span>
      <span>{duration}</span>
    </div>
  );
};

export default BuskingBadge;
