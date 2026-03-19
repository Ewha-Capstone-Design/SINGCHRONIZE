'use client';

import { cn } from '@/shared/lib/cn';
import type { SongUiType } from '@/entities/song/model/types';

type SongCardProps = {
  song: SongUiType;
  onClick?: (song: SongUiType) => void;
  className?: string;
};

const SongCard = ({ song, onClick, className }: SongCardProps) => {
  return (
    <div
      className={cn('w-35 text-left', onClick && 'cursor-pointer', className)}
      onClick={() => onClick?.(song)}
    >
      <div className='relative aspect-square w-full overflow-hidden rounded-10 bg-gray-800'>
        {song.thumbnail ? (
          <img src={song.thumbnail} alt={song.title} className='size-full object-cover' />
        ) : (
          <div className='size-full bg-white-10' />
        )}
      </div>

      <div className='mt-1.5 flex flex-col gap-0.5'>
        <p className='truncate typo-18sb text-white'>{song.title}</p>
        <p className='truncate typo-14r text-gray-300'>{song.artist}</p>
      </div>
    </div>
  );
};

export default SongCard;
