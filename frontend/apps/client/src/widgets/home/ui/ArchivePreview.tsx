'use client';

import { useMemo, useState } from 'react';
import { useNavigate } from '@/shared/lib/navigation';
import { SectionHeader, SelectChip } from '@/shared/components';
import type { GenreKey } from '@/shared/types/category';
import {
  GENRE_ITEMS,
  GENRE_API_LABEL,
  GENRE_LABEL_TO_KEY,
} from '@/shared/constants/genre';
import { SongListItem } from '@/entities/song/ui';
import { useArchivePreview } from '@/entities/archive';

type ArchiveFilter = 'all' | GenreKey;

type ArchivePreviewProps = {
  className?: string;
};

const ArchivePreview = ({ className }: ArchivePreviewProps) => {
  const { go, ROUTES } = useNavigate();
  const [filter, setFilter] = useState<ArchiveFilter>('all');

  const genreParam = filter !== 'all' ? GENRE_API_LABEL[filter] : undefined;
  const { data } = useArchivePreview(genreParam);

  const filterChips = useMemo(() => {
    const genreKeys = (data?.genreLabels ?? [])
      .map((l) => GENRE_LABEL_TO_KEY[l])
      .filter((k): k is GenreKey => !!k)
      .slice(0, 3);

    return [
      { key: 'all' as const, label: '전체' },
      ...genreKeys.map((key) => ({ key, label: GENRE_ITEMS[key].tabLabel })),
    ];
  }, [data?.genreLabels]);

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
        {(data?.items ?? []).map((song, idx) => (
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

