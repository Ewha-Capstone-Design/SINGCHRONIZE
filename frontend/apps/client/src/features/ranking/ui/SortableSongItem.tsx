import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { SongType } from '@/entities/song/model/types';
import { SongItem } from '@/shared/components';

type SortableSongItemProps = {
  song: SongType;
  index: number;
};

const SortableSongItem = ({ song, index }: SortableSongItemProps) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: song.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} className='flex justify-between items-center'>
      {/* 순위 */}
      <div className='text-32b'>{index + 1}</div>

      <SongItem
        song={song}
        onPlay={() => {
          // TODO: 미리듣기
        }}
        dragHandleProps={{
          ...attributes,
          ...listeners,
        }}
        className='touch-none'
      />
    </div>
  );
};

export default SortableSongItem;
