'use client';

import type { ButtonHTMLAttributes, MouseEvent } from 'react';
import { cn } from '@/shared/lib/cn';
import { IcClose } from '@/shared/assets/icons';

interface SelectChipProps extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  'children' | 'disabled'
> {
  label: string;
  selected?: boolean;
  removable?: boolean;
  onRemove?: () => void;
}

const SelectChip = ({
  label,
  selected = false,
  removable = false,
  onRemove,
  className,
  onClick,
  ...rest
}: SelectChipProps) => {
  const handleRemoveClick = (e: MouseEvent<HTMLSpanElement>) => {
    e.stopPropagation();
    onRemove?.();
  };

  return (
    <button
      type='button'
      onClick={onClick}
      className={cn(
        'px-5 py-2 inline-flex h-10 items-center justify-center border rounded-full cursor-pointer',
        removable ? 'gap-2' : 'gap-0',
        'transition-all duration-150',
        selected
          ? 'border-brand bg-yellow-500-30 text-brand'
          : 'border-transparent bg-gray-800 text-gray-500 hover:bg-gray-700 hover:text-white',
        className
      )}
      {...rest}
    >
      <span className='typo-16m whitespace-nowrap'>{label}</span>

      {removable ? (
        <span
          role='button'
          aria-label={`${label} 제거`}
          onClick={handleRemoveClick}
          className={cn(
            'inline-flex items-center justify-center',
            selected
              ? 'text-brand'
              : 'text-gray-100 group-hover:text-gray-100 group-active:text-gray-200'
          )}
        >
          <IcClose width={16} height={16} />
        </span>
      ) : null}
    </button>
  );
};

export default SelectChip;
