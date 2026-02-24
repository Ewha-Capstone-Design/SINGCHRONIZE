'use client';

import { cn } from '@/shared/lib/cn';
import { IcMore } from '@/shared/assets/icons';

type MoreActionButtonProps = {
  onClick?: () => void;
  className?: string;
};

const MoreActionButton = ({ onClick, className }: MoreActionButtonProps) => {
  return (
    <button
      type='button'
      aria-label='더보기'
      onClick={onClick}
      className={cn('inline-flex items-center justify-center', className)}
    >
      <IcMore />
    </button>
  );
};

export default MoreActionButton;
