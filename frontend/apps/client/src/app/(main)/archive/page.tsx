'use client';

import { useSectionTab } from '@/shared/hooks';
import { ArchiveBanner, ArchiveListWidget, ArchiveNavigator } from '@/widgets/archive/ui';
import { toArchiveSectionUi } from '@/entities/archive/model/mapper';
import { ArchiveTab } from '@/widgets/archive/model/types';

import { MOCK_ARCHIVE_HISTORY } from '@/entities/archive/model/mock';

const ArchivePage = () => {
  const { tab, tabs, changeTab } = useSectionTab({
    items: [
      { key: 'genre', label: '장르별' },
      { key: 'situation', label: '상황별' },
    ] as const,
    initialTab: 'genre',
  });

  // TODO: 쿼리 훅으로 교체
  const groups = [toArchiveSectionUi(MOCK_ARCHIVE_HISTORY)];

  return (
    <div className='flex-1 min-h-screen'>
      <ArchiveBanner variant='main' />
      <ArchiveNavigator
        tab={tab as ArchiveTab}
        tabs={tabs}
        onChangeTab={(nextTab) => changeTab(nextTab)}
      />
      <ArchiveListWidget groups={groups} />
    </div>
  );
};

export default ArchivePage;
