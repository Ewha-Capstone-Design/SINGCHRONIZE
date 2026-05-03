'use client';

import { cn } from '@/shared/lib/cn';
import { AppImage } from '@/shared/components';
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
        isSelected ? 'border border-brand' : 'border border-transparent',
      )}
    >
      {/* 썸네일 */}
      <div className='relative aspect-square inset-0'>
        <AppImage src={artist.imageUrl} alt={artist.name} fill className='object-cover' />

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
