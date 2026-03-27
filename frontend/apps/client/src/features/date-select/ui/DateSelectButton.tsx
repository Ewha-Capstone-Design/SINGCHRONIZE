'use client';

import { IcCalender } from '@/shared/assets/icons';
import { cn } from '@/shared/lib/cn';
import { format } from 'date-fns';

type DateSelectButtonProps = {
  selected?: Date;
  onClick: () => void;
};

const DateSelectButton = ({ selected, onClick }: DateSelectButtonProps) => {
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
      <span className={cn('typo-18sb', selected ? 'text-gray-500' : 'text-gray-100')}>
        {selected ? format(selected, 'yy년 MM월 dd일') : '날짜 선택하기'}
      </span>
    </button>
  );
};

export default DateSelectButton;
