'use client';

import { cn } from '@/shared/lib/cn';

interface FavoriteFolderCoverProps {
  images: string[];
  className?: string;
}

const FavoriteFolderCover = ({ images, className }: FavoriteFolderCoverProps) => {
  const coverImages = images.slice(0, 4);

  return (
    <div
      className={cn(
        'size-31.5 grid grid-cols-2 grid-rows-2 overflow-hidden rounded-10 shrink-0',
        className
      )}
    >
      {Array.from({ length: 4 }).map((_, index) => {
        const src = coverImages[index];

        return src ? (
          <img
            key={index}
            src={src}
            alt={`folder-cover-${index}`}
            className='size-full object-cover'
          />
        ) : (
          <div key={index} className='size-full bg-gray-700' />
        );
      })}
    </div>
  );
};

export default FavoriteFolderCover;
