'use client';

import { BuskingCard } from '@/entities/busking/ui';
import type { BuskingUiType } from '@/entities/busking/model/types';

const BuskingSection = ({
  title,
  items,
  onItemClick,
}: {
  title: string;
  items: BuskingUiType[];
  onItemClick?: (item: BuskingUiType) => void;
}) => {
  return (
    <section className='flex flex-col gap-4'>
      <h2 className='px-8 typo-28b text-gray-100'>{title}</h2>
      <div className='px-8 flex gap-4 overflow-x-auto scrollbar-hide'>
        {items.map((item) => (
          <BuskingCard
            key={item.id}
            variant='md'
            item={item}
            onClick={() => onItemClick?.(item)}
          />
        ))}
      </div>
    </section>
  );
};

export default BuskingSection;
