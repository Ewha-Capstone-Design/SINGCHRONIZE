'use client';

import { useEffect, useState } from 'react';
import { IcArrowRight } from '@/shared/assets/icons';
import { AppImage } from '@/shared/components';
import { cn } from '@/shared/lib/cn';
import type { SetlistType } from '@/entities/busking/model/types';

type SetlistCarouselProps = {
  items: SetlistType[];
  isAdvancing: boolean;
  isLastSong: boolean;
  onNext: () => void;
};

type AlbumCardProps = {
  item: SetlistType;
};

const CARD_WIDTH = 154;
const CARD_HEIGHT = 154;
const CARD_GAP_STEP = 112;
const ARROW_OFFSET = 52;

const SetlistCarousel = ({
  items,
  isAdvancing,
  isLastSong,
  onNext,
}: SetlistCarouselProps) => {
  const currentItemIndex = items.findIndex((item) => item.isCurrent);
  const syncedIndex = currentItemIndex >= 0 ? currentItemIndex : 0;

  const [activeIndex, setActiveIndex] = useState(syncedIndex);

  useEffect(() => {
    setActiveIndex(syncedIndex);
  }, [syncedIndex]);

  if (!items.length) return null;

  const currentSong = items[activeIndex];

  const isLastIndex = activeIndex === items.length - 1;

  const disabledNext = isAdvancing || isLastSong || isLastIndex;

  const trackWidth = (items.length - 1) * CARD_GAP_STEP + CARD_WIDTH;
  const translateX = activeIndex * CARD_GAP_STEP + CARD_WIDTH / 2;

  const handleNext = () => {
    if (disabledNext) return;

    onNext();
    setActiveIndex((prevIndex) => Math.min(items.length - 1, prevIndex + 1));
  };

  return (
    <section className='relative flex h-62 flex-col items-center justify-center overflow-hidden'>
      <div className='relative w-full overflow-hidden' style={{ height: CARD_HEIGHT }}>
        <div
          className='absolute top-0 transition-transform duration-300 ease-in-out'
          style={{
            left: '50%',
            width: trackWidth,
            height: CARD_HEIGHT,
            transform: `translateX(-${translateX}px)`,
          }}
        >
          {items.map((item, index) => {
            const distanceFromActive = Math.abs(index - activeIndex);
            const isActive = index === activeIndex;
            const isNearActive = distanceFromActive === 1;

            return (
              <div
                key={item.id}
                className={cn(
                  'absolute transition-all duration-300 ease-in-out',
                  isActive && 'z-10 scale-100 opacity-100',
                  isNearActive && 'z-0 scale-90 opacity-50',
                  !isActive &&
                    !isNearActive &&
                    'z-0 scale-90 opacity-0 pointer-events-none',
                )}
                style={{
                  left: index * CARD_GAP_STEP,
                  top: 0,
                  width: CARD_WIDTH,
                  height: CARD_HEIGHT,
                }}
              >
                <AlbumCard item={item} />
              </div>
            );
          })}
        </div>

        {!isLastIndex && (
          <button
            type='button'
            onClick={handleNext}
            aria-label='다음 곡으로'
            disabled={disabledNext}
            className={cn(
              'absolute top-1/2 z-20 flex size-12 -translate-x-1/2 -translate-y-1/2',
              'items-center justify-center',
              'disabled:cursor-not-allowed disabled:opacity-35',
            )}
            style={{ left: `calc(50% + ${CARD_WIDTH / 2 + ARROW_OFFSET}px)` }}
          >
            {isAdvancing ? (
              <span className='typo-18m'>...</span>
            ) : (
              <IcArrowRight className='text-white' />
            )}
          </button>
        )}
      </div>

      <div className='relative mt-2 text-center'>
        <p className='typo-18sb text-white'>
          {currentSong?.title ?? '현재 재생 중인 곡'}
        </p>
        <p className='typo-14r text-gray-300'>{currentSong?.artist ?? ''}</p>
      </div>
    </section>
  );
};

const AlbumCard = ({ item }: AlbumCardProps) => {
  return (
    <div className='relative size-full shrink-0 overflow-hidden rounded-10 bg-gray-800'>
      {item.thumbnail ? (
        <AppImage src={item.thumbnail} alt={item.title} fill className='object-cover' />
      ) : (
        <div className='flex size-full items-center justify-center px-4 text-center'>
          <span className='typo-14m text-gray-300'>{item.title}</span>
        </div>
      )}
    </div>
  );
};

export default SetlistCarousel;
