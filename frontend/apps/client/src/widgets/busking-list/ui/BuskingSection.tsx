'use client';

import { cn } from '@/shared/lib/cn';
import { useNavigate } from '@/shared/lib/navigation';
import { BuskingCard } from '@/entities/busking/ui';
import type { BuskingUiType } from '@/entities/busking/model/types';

interface BuskingSectionProps {
  title: string;
  items: BuskingUiType[];
  cardVariant?: 'sm' | 'md' | 'lg';
  titleTypo?: string;
  listClassName?: string;
  px?: number;
  onItemClick?: (item: BuskingUiType) => void;
}

const BuskingSection = ({
  title,
  items,
  cardVariant = 'md',
  titleTypo = 'typo-28b',
  listClassName,
  px = 8,
  onItemClick,
}: BuskingSectionProps) => {
  const { go, dynamic } = useNavigate();

  if (!items.length) return null;

  return (
    <section className='flex flex-col gap-4'>
      <h2
        className={cn('text-gray-100', titleTypo)}
        style={{ paddingLeft: `${px * 4}px`, paddingRight: `${px * 4}px` }}
      >
        {title}
      </h2>

      <div
        className={cn('flex gap-4 overflow-x-auto scrollbar-hide', listClassName)}
        style={{ paddingLeft: `${px * 4}px`, paddingRight: `${px * 4}px` }}
      >
        {items.map((item) => (
          <BuskingCard
            key={item.id}
            variant={cardVariant}
            item={item}
            onClick={() => {
              if (onItemClick) onItemClick(item);
              else go(dynamic.liveRoom(item.id, item.status));
            }}
          />
        ))}
      </div>
    </section>
  );
};

export default BuskingSection;
