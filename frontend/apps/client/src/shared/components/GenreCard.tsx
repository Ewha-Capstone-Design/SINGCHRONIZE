'use client';

import Image from 'next/image';
import { cn } from '@/shared/lib/cn';
import { GENRE_ITEMS } from '../constants/genre';
import type { GenreKey } from '../types/song';

type GenreCardProps = {
  genreKey: GenreKey;
  isSelected: boolean;
  onClick: () => void;
};

const GenreCard = ({ genreKey, isSelected, onClick }: GenreCardProps) => {
  const { label, imageUrl } = GENRE_ITEMS[genreKey];

  return (
    <button
      type='button'
      onClick={onClick}
      aria-pressed={isSelected}
      className={cn(
        'relative flex flex-col w-45 h-45 overflow-hidden rounded-10 aspect-square cursor-pointer transition-transform duration-200 hover:-translate-y-0.5',
        isSelected ? 'ring-2 ring-brand' : ''
      )}
    >
      <Image src={imageUrl} alt={genreKey} fill sizes='180px' loading='eager' />

      <div className='relative z-10 px-3.5 py-1.5'>
        <p className='whitespace-pre-line typo-28b text-left text-white'>{label}</p>
      </div>
    </button>
  );
};

export default GenreCard;
