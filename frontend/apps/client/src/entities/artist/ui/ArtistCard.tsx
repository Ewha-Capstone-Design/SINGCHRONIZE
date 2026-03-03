'use client';

import { cn } from '@/shared/lib/cn';
import type { ArtistUiType } from '../model/types';

type ArtistCardProps = {
  artist: ArtistUiType;
  isSelected: boolean;
  onToggle: (artistId: number) => void;
};

const ArtistCard = ({ artist, isSelected, onToggle }: ArtistCardProps) => {
  return (
    <button
      type='button'
      onClick={() => onToggle(artist.id)}
      className={cn(
        'relative w-37.5 h-37.5 overflow-hidden rounded-10 text-left transition',
        isSelected ? 'border border-brand' : 'border border-transparent'
      )}
    >
      {/* 썸네일 */}
      <div className='aspect-square inset-0'>
        {artist.imageUrl ? (
          <img
            src={artist.imageUrl}
            alt={artist.name}
            className='w-full h-full object-cover'
          />
        ) : (
          <div className='w-full h-full bg-white/10' />
        )}

        <div className='absolute inset-0 bg-black/60' />
      </div>

      <div className='absolute bottom-3 left-3.5 right-3.5 z-10'>
        <p className={cn('typo-24b', isSelected ? 'text-brand' : 'text-white')}>
          {artist.name}
        </p>
      </div>
    </button>
  );
};

export default ArtistCard;
