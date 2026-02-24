'use client';

import { cn } from '@/shared/lib/cn';

import { SITUATION_ITEMS } from '../constants/keyword';
import type { SituationKey } from '../types/song';

type SituationCardProps = {
  situationKey: SituationKey;
  isSelected: boolean;
  onClick: () => void;
};

const SituationCard = ({ situationKey, isSelected, onClick }: SituationCardProps) => {
  const { label, imageUrl } = SITUATION_ITEMS[situationKey];

  return (
    <button
      type='button'
      onClick={onClick}
      aria-pressed={isSelected}
      className={cn(
        'relative flex w-45 h-45 cursor-pointer flex-col items-start justify-end overflow-hidden rounded-10 aspect-square transition-transform duration-200 hover:-translate-y-0.5'
      )}
    >
      <div
        className='absolute inset-0 grayscale'
        style={{
          background: `lightgray url(${imageUrl}) 50% / cover no-repeat`,
        }}
      />

      <div
        className={cn(
          'absolute inset-0 transition-colors duration-200',
          isSelected ? 'bg-brand/60' : ''
        )}
      />

      <div className='relative z-10 flex w-full flex-col items-start justify-end px-4.25 py-3.5'>
        <p className='whitespace-pre-line typo-28b text-left text-white'>{label}</p>
      </div>
    </button>
  );
};

export default SituationCard;
