import { cn } from '@/shared/lib/cn';
import type { SongUiType } from '@/entities/song/model/types';
import { IcDrag, IcPlay } from '@/shared/assets/icons';

type SongItemProps = {
  song: SongUiType;
  onPlay?: () => void;
  dragHandleProps?: React.HTMLAttributes<HTMLButtonElement>;
  className?: string;
};

const SongItem = ({ song, onPlay, dragHandleProps, className }: SongItemProps) => {
  return (
    <div
      className={cn(
        'flex items-center w-[433] h-[91] bg-white-10 rounded-[10px]',
        className
      )}
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

      {/* 정보 + 버튼 */}
      <div className='flex flex-1 items-center px-[25] py-[18] gap-4 overflow-hidden'>
        {/* 텍스트 영역 */}
        <div className='flex flex-1 flex-col overflow-hidden'>
          <p className='typo-16b text-white truncate'>{song.title}</p>
          <p className='typo-14r text-gray-300 truncate'>{song.artist}</p>
        </div>

        {/* 버튼 */}
        <div className='flex items-center gap-4 shrink-0'>
          <button
            type='button'
            onClick={onPlay}
            className='text-white'
            aria-label='미리듣기'
          >
            <IcPlay />
          </button>

          <button
            type='button'
            {...dragHandleProps}
            className='cursor-grab'
            aria-label='순서 변경'
          >
            <IcDrag />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SongItem;
