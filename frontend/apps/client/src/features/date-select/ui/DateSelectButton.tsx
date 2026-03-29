'use client';

import { IcCalender } from '@/shared/assets/icons';
import { cn } from '@/shared/lib/cn';
import { format } from 'date-fns';

type DateSelectButtonProps = {
  selected?: Date;
  isOpen?: boolean;
  onClick: () => void;
};

const DateSelectButton = ({ selected, isOpen, onClick }: DateSelectButtonProps) => {
  const getText = () => {
    if (isOpen) return '00년 00월 00일';
    if (selected) return format(selected, 'yy년 MM월 dd일');
    return '날짜 선택하기';
  };

  const getTextColor = () => {
    if (isOpen) return 'text-gray-500';
    if (selected) return 'text-gray-100';
    return 'text-gray-100';
  };

  return (
    <button
      type='button'
      onClick={onClick}
      className={cn(
        'pl-3.5 pr-5 py-3 flex items-center gap-3 rounded-10',
        'bg-gray-800 transition-colors hover:bg-gray-800'
      )}
    >
      <IcCalender className='shrink-0' />
      <span className={cn('typo-18sb', getTextColor())}>{getText()}</span>
    </button>
  );
};

export default DateSelectButton;
