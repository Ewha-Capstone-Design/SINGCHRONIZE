'use client';

import { cn } from '@/shared/lib/cn';
import { AppImage } from '@/shared/components';

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
        className,
      )}
    >
      {Array.from({ length: 4 }).map((_, index) => {
        const src = coverImages[index];

        return (
          <div key={index} className='relative size-full'>
            <AppImage
              src={src}
              alt={`folder-cover-${index}`}
              fill
              className='object-cover'
            />
          </div>
        );
      })}
    </div>
  );
};

export default FavoriteFolderCover;
