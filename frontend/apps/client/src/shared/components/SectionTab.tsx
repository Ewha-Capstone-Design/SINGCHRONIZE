'use client';

import { cn } from '@/shared/lib/cn';

export type SectionTabItem = {
  key: string;
  label: string;
};

type SectionTabProps = {
  items: readonly SectionTabItem[];
  value: string;
  onChange: (value: string) => void;
};

const SectionTab = ({ items, value, onChange }: SectionTabProps) => {
  return (
    <div className={cn('flex gap-5')}>
      {items.map((item) => {
        const isActive = item.key === value;

        return (
          <button
            key={item.key}
            type='button'
            role='tab'
            aria-selected={isActive}
            onClick={() => onChange(item.key)}
            className={cn(
              'flex flex-col gap-[2] transition-colors',
              isActive ? 'text-white' : 'text-gray-600'
            )}
          >
            <span className='typo-28b'>{item.label}</span>

            {isActive ? <span className='w-full h-0.5 rounded-full bg-brand' /> : null}
          </button>
        );
      })}
    </div>
  );
};

export default SectionTab;
