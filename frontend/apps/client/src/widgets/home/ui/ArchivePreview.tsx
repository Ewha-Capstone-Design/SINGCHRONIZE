'use client';

import { useMemo, useState } from 'react';
import { useNavigate } from '@/shared/lib/navigation';
import { SectionHeader, SelectChip } from '@/shared/components';
import { GenreKey } from '@/shared/types/category';
import { GENRE_ITEMS } from '@/shared/constants/genre';
import { SongListItem } from '@/entities/song/ui';

import { MOCK_ARCHIVE_UI } from '@/entities/archive/model/mock';

type ArchiveFilter = 'all' | GenreKey;

type ArchivePreviewProps = {
  className?: string;
};

export const ArchivePreview = ({ className }: ArchivePreviewProps) => {
  const { go, ROUTES } = useNavigate();

  const [filter, setFilter] = useState<ArchiveFilter>('all');

  // TODO: 추후 API로 필터링
  const filterChips = useMemo(() => {
    const genreKeys = MOCK_ARCHIVE_UI.genres.slice(0, 3);

    return [
      { key: 'all' as const, label: '전체' },
      ...genreKeys.map((key) => ({
        key,
        label: GENRE_ITEMS[key].tabLabel,
      })),
    ];
  }, []);

  const items = useMemo(() => {
    return MOCK_ARCHIVE_UI.items;
  }, [filter]);

  return (
    <section className={className}>
      <SectionHeader title='나의 아카이브' onMoreClick={() => go(ROUTES.archive)} />

      <div className='mt-4 flex flex-wrap items-center gap-2'>
        {filterChips.map((chip) => (
          <SelectChip
            key={chip.key}
            label={chip.label}
            selected={chip.key === filter}
            onClick={() => setFilter(chip.key)}
          />
        ))}
      </div>

      <div className='mt-4 flex flex-col gap-3'>
        {items.map((song, idx) => (
          <SongListItem
            key={song.id}
            variant='list5'
            rank={idx + 1}
            title={song.title}
            artist={song.artist}
            thumbnail={song.thumbnail ?? ''}
            matchRate={song.matchRate}
            isLiked={song.isLiked}
          />
        ))}
      </div>
    </section>
  );
};

export default ArchivePreview;
