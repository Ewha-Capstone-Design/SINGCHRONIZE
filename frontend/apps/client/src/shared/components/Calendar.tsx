'use client';

import { useState } from 'react';

import {
  addMonths,
  subMonths,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  format,
} from 'date-fns';
import { ko } from 'date-fns/locale';
import { IcBack } from '../assets/icons';
import { cn } from '../lib/cn';

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];

type CalendarProps = {
  selected?: Date;
  onSelect: (date: Date) => void;
};

const Calendar = ({ selected, onSelect }: CalendarProps) => {
  const [currentMonth, setCurrentMonth] = useState(selected ?? new Date());

  const days = eachDayOfInterval({
    start: startOfWeek(startOfMonth(currentMonth)),
    end: endOfWeek(endOfMonth(currentMonth)),
  });

  return (
    <div className='flex flex-col'>
      {/* 헤더 */}
      <div className='relative pb-4 flex items-center justify-center h-10'>
        <button
          type='button'
          onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
          className='absolute left-0 flex items-center justify-center w-8 h-8'
        >
          <IcBack />
        </button>

        <span className='typo-18sb text-white'>
          {format(currentMonth, 'yyyy년 M월', { locale: ko })}
        </span>

        <button
          type='button'
          onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
          className='absolute right-0 flex items-center justify-center w-8 h-8'
        >
          <IcBack className='rotate-180' />
        </button>
      </div>

      {/* 요일 */}
      <div className='py-1 grid grid-cols-7'>
        {WEEKDAYS.map((day) => (
          <div
            key={day}
            className='flex items-center justify-center w-10 h-7 typo-14r text-gray-500 select-none'
          >
            {day}
          </div>
        ))}
      </div>

      {/* 날짜 */}
      <div className='py-2 grid grid-cols-7 gap-y-2'>
        {days.map((day) => {
          const isCurrentMonth = isSameMonth(day, currentMonth);
          const isSelected = selected ? isSameDay(day, selected) : false;

          return (
            <button
              key={day.toISOString()}
              type='button'
              onClick={() => isCurrentMonth && onSelect(day)}
              className={cn(
                'relative flex items-center justify-center w-10 h-8',
                'typo-14r transition-colors',
                isCurrentMonth ? 'text-gray-300' : 'invisible pointer-events-none',
                isSelected && 'text-black'
              )}
            >
              {isSelected && (
                <span className='absolute inset-0 m-auto w-8 h-8 rounded-full bg-brand' />
              )}
              <span className='relative z-10'>{format(day, 'd')}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default Calendar;
