import { cn } from '@/shared/lib/cn';
import type { SongUiType } from '@/entities/song/model/types';
import { IcDrag, IcPlay } from '@/shared/assets/icons';

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
      <div className='h-full aspect-square rounded-l-[10px] overflow-hidden shrink-0'>
        {song.thumbnail ? (
          <img
            src={song.thumbnail}
            alt={song.title}
            className='w-full h-full object-cover'
          />
        ) : null}
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
