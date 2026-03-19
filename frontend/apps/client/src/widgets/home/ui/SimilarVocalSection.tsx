'use client';

import { cn } from '@/shared/lib/cn';
import { SectionHeader, SectionTab } from '@/shared/components';
import { useSectionTab } from '@/shared/hooks';
import { SongCard } from '@/entities/song/ui';
import type { SongUiType } from '@/entities/song/model/types';

import { MOCK_SONG_LIST } from '@/entities/song/model/mock';

type RangeKey = 'today' | 'week' | 'month';

type SimilarVocalSectionProps = {
  onSongClick: (song: SongUiType) => void;
};

const SimilarVocalSection = ({ onSongClick }: SimilarVocalSectionProps) => {
  const { tab, tabs, changeTab } = useSectionTab({
    items: [
      { key: 'today', label: '오늘' },
      { key: 'week', label: '이번주' },
      { key: 'month', label: '이번달' },
    ],
    initialTab: 'today',
  });

  const itemsByRange = {
    today: MOCK_SONG_LIST,
    week: MOCK_SONG_LIST,
    month: MOCK_SONG_LIST,
  } as const;

  const items = itemsByRange[tab as RangeKey] ?? [];

  return (
    <section className={cn('w-full')}>
      <div className='flex flex-col gap-3'>
        <SectionHeader title='나랑 닮은 목소리의 pick!' textClassName='typo-28b' />
        <SectionTab
          items={tabs}
          value={tab}
          onChange={changeTab}
          textClassName='typo-20sb'
        />
      </div>

      <div className='mt-6 w-full overflow-x-auto scrollbar-hide'>
        <div className='flex w-max gap-4'>
          {items.map((song) => (
            <SongCard key={song.id} song={song} onClick={onSongClick} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default SimilarVocalSection;
