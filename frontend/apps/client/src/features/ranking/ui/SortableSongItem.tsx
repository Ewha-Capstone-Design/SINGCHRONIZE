import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { cn } from '@/shared/lib/cn';
import { IcTrash } from '@/shared/assets/icons';
import type { SongUiType } from '@/entities/song/model/types';
import { SongItem } from '@/entities/song/ui';

type SortableSongItemProps = {
  song: SongUiType;
  index: number;
  onRemove?: (songId: string) => void;
};

const SortableSongItem = ({ song, index, onRemove }: SortableSongItemProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: song.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} className='flex justify-between items-center'>
      {/* 순위 */}
      <div className='typo-32b text-white'>{index + 1}</div>

      <SongItem
        song={song}
        showPlayButton={false}
        actionSlot={
          onRemove ? (
            <button
              type='button'
              onClick={() => onRemove(String(song.id))}
              className='text-gray-300'
              aria-label='곡 삭제'
            >
              <IcTrash />
            </button>
          ) : null
        }
        dragHandleProps={{
          ...attributes,
          ...listeners,
        }}
        className={cn('touch-none', isDragging && 'border border-brand rounded-[10px]')}
      />
    </div>
  );
};

export default SortableSongItem;
