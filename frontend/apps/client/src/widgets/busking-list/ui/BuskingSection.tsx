'use client';

import { cn } from '@/shared/lib/cn';
import { BuskingCard } from '@/entities/busking/ui';
import type { BuskingUiType } from '@/entities/busking/model/types';

interface BuskingSectionProps {
  title: string;
  items: BuskingUiType[];
  cardVariant?: 'sm' | 'md' | 'lg';
  titleTypo?: string;
  listClassName?: string;
  onItemClick?: (item: BuskingUiType) => void;
}

const BuskingSection = ({
  title,
  items,
  cardVariant = 'md',
  titleTypo = 'typo-28b',
  listClassName,
  onItemClick,
}: BuskingSectionProps) => {
  return (
    <section className='flex flex-col gap-4'>
      <h2 className={cn('px-8 text-gray-100', titleTypo)}>{title}</h2>

      <div
        className={cn('px-8 flex gap-4 overflow-x-auto scrollbar-hide', listClassName)}
      >
        {items.map((item) => (
          <BuskingCard
            key={item.id}
            variant={cardVariant}
            item={item}
            onClick={() => onItemClick?.(item)}
          />
        ))}
      </div>
    </section>
  );
};

export default BuskingSection;
