import { useEffect, useState } from 'react';
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
import { restrictToVerticalAxis } from '@dnd-kit/modifiers';

import SortableSongItem from './SortableSongItem';
import { SongUiType } from '@/entities/song/model/types';

type SortableSongListProps = {
  initialSongs: SongUiType[];
  onChange?: (songs: SongUiType[]) => void;
  onRemove?: (songId: string) => void;
};

const SortableSongList = ({
  initialSongs,
  onChange,
  onRemove,
}: SortableSongListProps) => {
  const [songs, setSongs] = useState<SongUiType[]>(initialSongs);
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(useSensor(PointerSensor));

  useEffect(() => {
    setSongs(initialSongs);
  }, [initialSongs]);

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

  const handleRemove = (songId: string) => {
    setSongs((prev) => {
      const next = prev.filter((song) => song.id !== songId);
      onChange?.(next);
      onRemove?.(songId);
      return next;
    });
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      modifiers={[restrictToVerticalAxis]}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={songs.map((s) => s.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className='flex flex-col gap-5 w-full'>
          {songs.map((song, index) => (
            <SortableSongItem
              key={song.id}
              song={song}
              index={index}
              onRemove={handleRemove}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
};

export default SortableSongList;
