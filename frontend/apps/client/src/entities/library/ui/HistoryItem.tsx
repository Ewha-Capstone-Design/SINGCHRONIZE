'use client';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@singchronize/ui';
import { IcMore } from '@/shared/assets/icons';
import { cn } from '@/shared/lib/cn';
import { AppImage } from '@/shared/components';
import type { HistoryItemUiType } from '../model/types';
import { getHistoryTagLabel } from '../model/tags';

type HistoryItemProps = {
  item: HistoryItemUiType;
  onEditClick?: (historyId: string) => void;
  onDeleteClick?: (historyId: string) => void;
};

const HistoryItem = ({ item, onEditClick, onDeleteClick }: HistoryItemProps) => {
  const hasTags = (item.tags?.length ?? 0) > 0;
  const hasMemo = Boolean(item.memo && item.memo.trim().length > 0);

  return (
    <article
      className={cn(
        'px-10 py-7 flex gap-6 bg-gray-900 border-2 border-gray-800 rounded-10',
      )}
    >
      <div className='relative size-23 shrink-0 overflow-hidden rounded-10'>
        <AppImage src={item.thumbnail} alt={item.title} fill className='object-cover' />
      </div>

      <div className='flex flex-1 flex-col gap-4 min-w-0'>
        {/* 음원 정보 */}
        <div className='flex justify-between gap-6'>
          <div className='flex flex-1 flex-col min-w-0'>
            <h3 className='typo-24b text-white truncate'>{item.title}</h3>
            <p className='mt-0.5 typo-16r text-gray-200 truncate'>{item.artist}</p>
            <p className='mt-2 typo-16r text-gray-400'>{item.date}</p>
          </div>

          {/* 더보기 드롭다운 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <IcMore className='rotate-90 cursor-pointer' />
            </DropdownMenuTrigger>
            <DropdownMenuContent
              side='bottom'
              align='end'
              sideOffset={12}
              alignOffset={-28}
            >
              <DropdownMenuItem onSelect={() => onEditClick?.(item.historyId)}>
                기록 수정하기
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => onDeleteClick?.(item.historyId)}>
                기록 삭제하기
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* 태그 */}
        {hasTags && (
          <div className='flex flex-col gap-2'>
            <h4 className='typo-18sb text-gray-200'>평가</h4>
            <div className='flex gap-2'>
              {item.tags.map((tag) => (
                <span
                  key={tag}
                  className={cn(
                    'px-5 py-2 bg-gray-800 rounded-full',
                    'typo-16m text-gray-100',
                  )}
                >
                  {getHistoryTagLabel(tag)}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 메모 */}
        {hasMemo && (
          <div className='flex flex-col gap-2'>
            <h4 className='typo-18sb text-gray-200'>메모</h4>
            <div className='px-6 py-4 bg-gray-800 rounded-10'>
              <p className='typo-16r text-gray-100 whitespace-pre-wrap'>{item.memo}</p>
            </div>
          </div>
        )}
      </div>
    </article>
  );
};

export default HistoryItem;
