'use client';

import { SectionTab } from '@/shared/components';
import { useSectionTab } from '@/shared/hooks';
import {
  LibraryBanner,
  LibraryFavoriteList,
  LibraryHistoryList,
} from '@/widgets/library/ui';

const LibraryPage = () => {
  const { tab, tabs, changeTab } = useSectionTab({
    items: [
      { key: 'favorite', label: '찜 리스트' },
      { key: 'history', label: '보컬 기록' },
    ] as const,
    initialTab: 'favorite',
  });

  return (
    <div className='flex-1 min-h-screen'>
      <LibraryBanner />
      <div className='px-8'>
        <SectionTab items={tabs} value={tab} onChange={(nextTab) => changeTab(nextTab)} />
        {tab == 'favorite' ? <LibraryFavoriteList /> : <LibraryHistoryList />}
      </div>
    </div>
  );
};

export default LibraryPage;
