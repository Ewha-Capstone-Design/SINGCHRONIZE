'use client';

import type { ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';

type SectionHeaderProps = {
  title: string;
  description?: string;
  right?: ReactNode;
  onMoreClick?: () => void;
  className?: string;
  textClassName?: string;
};

const SectionHeader = ({
  title,
  description,
  right,
  onMoreClick,
  className,
  textClassName,
}: SectionHeaderProps) => {
  const titleClassName = textClassName ?? 'typo-24b';

  return (
    <div className={cn('flex items-end justify-between gap-4', className)}>
      <div className='flex flex-col'>
        <h2 className={cn(titleClassName, 'text-white')}>{title}</h2>
        {description ? <p className='typo-16r text-gray-400'>{description}</p> : null}
      </div>

      <div className='flex items-center gap-1'>
        {right}
        {onMoreClick ? (
          <button type='button' onClick={onMoreClick} className='typo-16r text-gray-300'>
            더보기
          </button>
        ) : null}
      </div>
    </div>
  );
};

export default SectionHeader;
