import { cn } from '@/shared/lib/cn';
import { IcDrag, IcPlay } from '@/shared/assets/icons';
import { AppImage } from '@/shared/components';
import type { SongUiType } from '@/entities/song/model/types';

type SongItemProps = {
  song: SongUiType;
  onPlay?: () => void;
  showPlayButton?: boolean;
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
  actionSlot?: React.ReactNode;
  className?: string;
};

const SongItem = ({
  song,
  onPlay,
  showPlayButton = true,
  dragHandleProps,
  actionSlot,
  className,
}: SongItemProps) => {
  return (
    <div
      className={cn('flex items-center w-108 h-22.5 bg-white-10 rounded-10', className)}
    >
      {/* 앨범 이미지 */}
      <div className='relative h-full aspect-square rounded-l-[10px] overflow-hidden shrink-0'>
        <AppImage src={song.thumbnail} alt={song.title} fill className='object-cover' />
      </div>

      <div className='px-6.25 py-4.5 flex flex-1 items-center gap-4 overflow-hidden'>
        <div className='flex flex-1 flex-col overflow-hidden'>
          <p className='typo-16b text-white truncate'>{song.title}</p>
          <p className='typo-14r text-gray-300 truncate'>{song.artist}</p>
        </div>

        {/* 버튼 */}
        <div className='flex items-center gap-4 shrink-0'>
          {actionSlot}

          {showPlayButton && onPlay && (
            <button
              type='button'
              onClick={onPlay}
              className='text-white'
              aria-label='미리듣기'
            >
              <IcPlay />
            </button>
          )}

          {dragHandleProps && (
            <button
              type='button'
              {...dragHandleProps}
              className='cursor-grab active:cursor-grabbing'
              aria-label='순서 변경'
            >
              <IcDrag />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SongItem;
