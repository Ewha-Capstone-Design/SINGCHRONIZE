'use client';

import { PageBanner, SectionTab } from '@/shared/components';
import { useSectionTab } from '@/shared/hooks';
import { LibraryFavoriteList, LibraryHistoryList } from '@/widgets/library';

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
      <PageBanner
        category='노래방 키트'
        title='노래방에서 찜한 노래와 보컬 기록을 확인하며 노래해보세요!'
      />
      <div className='px-8'>
        <SectionTab items={tabs} value={tab} onChange={(nextTab) => changeTab(nextTab)} />
        {tab == 'favorite' ? <LibraryFavoriteList /> : <LibraryHistoryList />}
      </div>
    </div>
  );
};

export default LibraryPage;
