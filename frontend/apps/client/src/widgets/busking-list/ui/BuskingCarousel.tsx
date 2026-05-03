'use client';

import { useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { IcArrowRight } from '@/shared/assets/icons';
import { useNavigate } from '@/shared/lib/navigation';
import { BuskingCard } from '@/entities/busking/ui';
import type { BuskingUiType } from '@/entities/busking/model/types';

const CARD_W = 530;
const CARD_H = 300;
const STEP = 280;

const BuskingCarousel = ({ items }: { items: BuskingUiType[] }) => {
  const [index, setIndex] = useState(0);
  const { dynamic } = useNavigate();

  if (!items.length) return null;

  const prev = () => setIndex((i) => Math.max(0, i - 1));
  const next = () => setIndex((i) => Math.min(items.length - 1, i + 1));

  const trackW = (items.length - 1) * STEP + CARD_W;
  const translateX = index * STEP + CARD_W / 2;

  return (
    <div className='relative w-full overflow-hidden' style={{ height: CARD_H }}>
      {/* 트랙 */}
      <div
        className='absolute top-0 transition-transform duration-300 ease-in-out'
        style={{
          left: '50%',
          transform: `translateX(-${translateX}px)`,
          width: trackW,
          height: CARD_H,
        }}
      >
        {items.map((item, i) => (
          <div
            key={item.id}
            className={cn(
              'absolute transition-all duration-300',
              i === index
                ? 'z-10'
                : Math.abs(i - index) === 1
                  ? 'z-0 opacity-50 scale-75'
                  : 'z-0 opacity-0 scale-75 pointer-events-none',
            )}
            style={{ left: i * STEP, top: 0, width: CARD_W, height: CARD_H }}
          >
            <BuskingCard
              variant='lg'
              item={item}
              onClick={() => {
                if (i !== index) {
                  setIndex(i);
                } else {
                  window.location.href = dynamic.liveRoom(item.id, item.status);
                }
              }}
            />
          </div>
        ))}
      </div>

      {/* 이전 버튼 */}
      {index > 0 && (
        <button
          type='button'
          onClick={prev}
          aria-label='이전'
          className='absolute top-1/2 -translate-x-1/2 -translate-y-1/2 z-20 size-12 rounded-full bg-white flex items-center justify-center shadow-lg'
          style={{ left: `calc(50% - ${CARD_W / 2 + 48}px)` }}
        >
          <IcArrowRight className='rotate-180 text-black' />
        </button>
      )}

      {/* 다음 버튼 */}
      {index < items.length - 1 && (
        <button
          type='button'
          onClick={next}
          aria-label='다음'
          className='absolute top-1/2 -translate-x-1/2 -translate-y-1/2 z-20 size-12 rounded-full bg-white flex items-center justify-center shadow-lg'
          style={{ left: `calc(50% + ${CARD_W / 2 + 48}px)` }}
        >
          <IcArrowRight className='text-black' />
        </button>
      )}
    </div>
  );
};

export default BuskingCarousel;
