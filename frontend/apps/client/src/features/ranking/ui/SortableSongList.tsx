import { useState } from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable';

import SortableSongItem from './SortableSongItem';
import { SongUiType } from '@/entities/song/model/types';

type SortableSongListProps = {
  initialSongs: SongUiType[];
  onChange?: (songs: SongUiType[]) => void;
};

const SortableSongList = ({ initialSongs, onChange }: SortableSongListProps) => {
  const [songs, setSongs] = useState<SongUiType[]>(initialSongs);
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(useSensor(PointerSensor));

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    setActiveId(null);

    if (!over || active.id === over.id) return;

    setSongs((prev) => {
      const oldIndex = prev.findIndex((s) => s.id === active.id);
      const newIndex = prev.findIndex((s) => s.id === over.id);
      const next = arrayMove(prev, oldIndex, newIndex);
      onChange?.(next);
      return next;
    });
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={songs.map((s) => s.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className='flex flex-col gap-5 w-full'>
          {songs.map((song, index) => (
            <SortableSongItem key={song.id} song={song} index={index} />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
};

export default SortableSongList;
