'use client';

import { cn } from '@/shared/lib/cn';
import { AppImage } from '@/shared/components';

interface FavoriteFolderCoverProps {
  images: string[];
  className?: string;
}

const gridConfig = {
  0: 'grid-cols-1 grid-rows-1',
  1: 'grid-cols-1 grid-rows-1',
  2: 'grid-cols-2 grid-rows-1',
  3: 'grid-cols-2 grid-rows-2',
  4: 'grid-cols-2 grid-rows-2',
} as const;

const FavoriteFolderCover = ({ images, className }: FavoriteFolderCoverProps) => {
  const coverImages = images.slice(0, 4);
  const count = coverImages.length;

  if (count === 0) {
    return <div className={cn('size-31.5 rounded-10 shrink-0 bg-gray-800', className)} />;
  }

  return (
    <div
      className={cn(
        'size-31.5 grid overflow-hidden rounded-10 shrink-0',
        gridConfig[count as keyof typeof gridConfig],
        className,
      )}
    >
      {coverImages.map((src, index) => (
        <div
          key={index}
          className={cn('relative size-full', count === 3 && index === 2 && 'col-span-2')}
        >
          <AppImage
            src={src}
            alt={`folder-cover-${index}`}
            fill
            className='object-cover'
          />
        </div>
      ))}
    </div>
  );
};

export default FavoriteFolderCover;
