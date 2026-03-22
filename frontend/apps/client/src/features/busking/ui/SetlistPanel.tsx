'use client';

import { cn } from '@/shared/lib/cn';
import type { SetlistType } from '@/entities/busking/model/types';

const SetlistPanel = ({ title, items }: { title: string; items: SetlistType[] }) => {
  return (
    <div className='p-4 flex flex-col gap-4 w-72 rounded-10 bg-black-80 shrink-0'>
      <div>
        <p className='typo-12r text-gray-500'>버스킹 제목</p>
        <p className='typo-18sb text-white'>{title}</p>
      </div>

      <div className='flex flex-col gap-1'>
        {items.map((item) => (
          <div
            key={item.rank}
            className={cn(
              'px-3 flex items-center gap-2 h-15 rounded-10',
              item.isCurrent ? 'bg-yellow-500-30' : 'bg-gray-700'
            )}
          >
            <span className='w-3 typo-16m text-gray-100 shrink-0'>{item.rank}</span>
            <div className='size-8 rounded-sm bg-gray-400 shrink-0 overflow-hidden'>
              {item.thumbnail && (
                <img
                  src={item.thumbnail}
                  alt={item.title}
                  className='size-full object-cover'
                />
              )}
            </div>
            <div className='flex flex-col min-w-0'>
              <span className='typo-14r text-white truncate'>{item.title}</span>
              <span className='typo-12r text-gray-400 truncate'>{item.artist}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SetlistPanel;
