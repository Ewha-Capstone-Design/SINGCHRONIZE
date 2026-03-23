'use client';

import { BuskingResultItem } from '@/entities/busking/ui';
import type { BuskingResultItemType } from '@/entities/busking/model/types';

type BuskingResultListProps = {
  streamerName: string;
  items: BuskingResultItemType[];
};

const BuskingResultList = ({ streamerName, items }: BuskingResultListProps) => {
  return (
    <div className='relative mx-auto px-12 py-16 flex w-full max-w-270 flex-col'>
      <h1 className='text-center typo-32b text-white'>
        {streamerName}님의 라이브 버스킹 결과를 살펴보세요!
      </h1>

      <ul className='mt-14 flex flex-col gap-8'>
        {items.map((item) => (
          <BuskingResultItem key={String(item.id)} item={item} />
        ))}
      </ul>
    </div>
  );
};

export default BuskingResultList;
