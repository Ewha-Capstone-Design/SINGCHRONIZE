'use client';

import { useNavigate } from '@/shared/lib/navigation';
import { SituationCard, GenreCard, SectionTab } from '@/shared/components';
import type { SectionTabItem } from '@/shared/components/SectionTab';
import type { SituationKey, GenreKey } from '@/shared/types/category';
import { SITUATION_KEYS } from '@/shared/constants/situation';
import { GENRE_KEYS } from '@/shared/constants/genre';
import { ArchiveTab } from '../model/types';

type ArchiveNavigatorProps = {
  tab: ArchiveTab;
  tabs: readonly SectionTabItem[];
  onChangeTab: (tab: ArchiveTab) => void;
};

const ArchiveNavigator = ({ tab, tabs, onChangeTab }: ArchiveNavigatorProps) => {
  const { go, dynamic } = useNavigate();

  const handleClickCategory = (key: GenreKey | SituationKey) => {
    go(dynamic.archiveCategory(key));
  };

  return (
    <section className='pl-8 flex flex-col gap-4 w-full max-w-full overflow-hidden'>
      <SectionTab
        items={tabs}
        value={tab}
        onChange={(value) => onChangeTab(value as ArchiveTab)}
      />

      <div className='pr-8 flex gap-5 w-0 min-w-full overflow-x-auto scrollbar-hide'>
        {tab === 'genre'
          ? GENRE_KEYS.map((genreKey) => (
              <GenreCard
                key={genreKey}
                genreKey={genreKey}
                onClick={() => handleClickCategory(genreKey)}
              />
            ))
          : SITUATION_KEYS.map((situationKey) => (
              <SituationCard
                key={situationKey}
                situationKey={situationKey}
                onClick={() => handleClickCategory(situationKey)}
              />
            ))}
      </div>
    </section>
  );
};

export default ArchiveNavigator;
