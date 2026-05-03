'use client';

import { AppImage } from '@/shared/components';
import type { BuskingResultItemType } from '../model/types';

const clampPercent = (v: number) => Math.min(100, Math.max(0, Math.round(v)));

type BuskingResultItemProps = { item: BuskingResultItemType };

const BuskingResultItem = ({ item }: BuskingResultItemProps) => {
  const left = clampPercent(item.votePercent);
  const right = 100 - left;

  return (
    <li className='flex items-center gap-10'>
      {/* 순위 */}
      <div className='w-6 text-center typo-32b text-gray-200'>{item.rank}</div>

      {/* 카드 */}
      <div className='px-6 flex items-center gap-9 w-full h-29 rounded-10 bg-gray-700'>
        <div className='flex gap-5'>
          {/* 썸네일 */}
          <div className='relative size-19 shrink-0 overflow-hidden rounded-sm'>
            <AppImage
              src={item.thumbnail}
              alt={item.title}
              fill
              className='object-cover'
            />
          </div>

          {/* 곡명 / 아티스트 */}
          <div className='flex flex-col justify-center min-w-0 w-30 shrink-0'>
            <p className='truncate typo-20sb text-white'>{item.title}</p>
            <p className='truncate typo-20r text-gray-400'>{item.artist}</p>
          </div>
        </div>

        {/* 바 + 설명 */}
        <div className='flex flex-1 flex-col gap-2 min-w-0'>
          <div className='relative h-10 w-full overflow-hidden rounded-10 bg-gray-800'>
            <div
              className='absolute left-0 top-0 h-full bg-brand'
              style={{ width: `${left}%` }}
            />
            <div className='relative z-1 flex h-full items-center justify-between px-4'>
              <span className='typo-18sb text-black'>{left}%</span>
              <span className='typo-18sb text-gray-200'>{right}%</span>
            </div>
          </div>

          <p className='typo-18sb text-gray-300'>
            시청자 {left}%가 당신의 목소리와 잘 어울린다고 투표했어요
          </p>
        </div>
      </div>
    </li>
  );
};

export default BuskingResultItem;
