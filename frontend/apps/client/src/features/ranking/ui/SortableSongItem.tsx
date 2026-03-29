import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Tooltip, TooltipContent, TooltipTrigger } from '@singchronize/ui';
import { cn } from '@/shared/lib/cn';
import { IcTrash, IcPlay } from '@/shared/assets/icons';
import type { SongUiType } from '@/entities/song/model/types';
import { SongItem } from '@/entities/song/ui';

type SortableSongItemVariant = 'delete' | 'play';

type SortableSongItemProps = {
  song: SongUiType;
  index: number;
  variant?: SortableSongItemVariant;
  onRemove?: (songId: string) => void;
  onPlay?: (song: SongUiType) => void;
};

const SortableSongItem = ({
  song,
  index,
  variant = 'delete',
  onRemove,
  onPlay,
}: SortableSongItemProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: song.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const actionSlot =
    variant === 'play' ? (
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type='button'
            onClick={() => onPlay?.(song)}
            className='text-gray-300'
            aria-label='곡 재생'
          >
            <IcPlay />
          </button>
        </TooltipTrigger>
        <TooltipContent sideOffset={4}>영상으로 전체 곡 듣기</TooltipContent>
      </Tooltip>
    ) : onRemove ? (
      <button
        type='button'
        onClick={() => onRemove(String(song.id))}
        className='text-gray-300'
        aria-label='곡 삭제'
      >
        <IcTrash />
      </button>
    ) : null;

  return (
    <div ref={setNodeRef} style={style} className='flex justify-between items-center'>
      <div className='typo-32b text-white'>{index + 1}</div>

      <SongItem
        song={song}
        showPlayButton={false}
        actionSlot={actionSlot}
        dragHandleProps={{ ...attributes, ...listeners }}
        className={cn('touch-none', isDragging && 'border border-brand rounded-[10px]')}
      />
    </div>
  );
};

export default SortableSongItem;
