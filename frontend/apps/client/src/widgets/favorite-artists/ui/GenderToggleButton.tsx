'use client';

import { cn } from '@/shared/lib/cn';
import { GenderType } from '@/entities/artist/model/types';

type GenderToggleButtonProps = {
  value: GenderType;
  onChange: (next: GenderType) => void;
  className?: string;
};

const GenderToggleButton = ({ value, onChange, className }: GenderToggleButtonProps) => {
  const isMale = value === 'male';

  return (
    <div
      className={cn(
        'relative px-2 py-1.5 inline-flex items-center gap-1 rounded-full',
        className
      )}
      role='tablist'
    >
      <span
        aria-hidden='true'
        className={cn(
          'absolute h-[calc(100%-12px)] w-14 rounded-full bg-gray-100',
          'transition-transform duration-200 ease-out',
          isMale ? 'translate-x-0' : 'translate-x-[calc(100%+4px)]'
        )}
      />

      <button
        type='button'
        role='tab'
        aria-selected={isMale}
        onClick={() => onChange('male')}
        className={cn(
          'relative z-10 px-3.75 py-1.5 w-14 rounded-full typo-14r transition-colors',
          isMale ? 'text-black' : 'text-gray-500'
        )}
      >
        남성
      </button>

      <button
        type='button'
        role='tab'
        aria-selected={!isMale}
        onClick={() => onChange('female')}
        className={cn(
          'relative z-10 px-3.75 py-1.5 w-14 rounded-full typo-14r transition-colors',
          !isMale ? 'text-black' : 'text-gray-500'
        )}
      >
        여성
      </button>
    </div>
  );
};

export default GenderToggleButton;
