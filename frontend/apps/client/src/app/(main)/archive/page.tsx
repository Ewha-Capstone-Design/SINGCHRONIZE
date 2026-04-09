'use client';

import { useSectionTab, useDateSelect } from '@/shared/hooks';
import { toLocalDateString } from '@/shared/lib/formatTime';
import { ArchiveBanner, ArchiveListWidget, ArchiveNavigator } from '@/widgets/archive/ui';
import { ArchiveTab } from '@/widgets/archive/model/types';

import { useRecommendationArchive } from '@/entities/archive';

const ArchivePage = () => {
  const { tab, tabs, changeTab } = useSectionTab({
    items: [
      { key: 'genre', label: '장르별' },
      { key: 'situation', label: '상황별' },
    ] as const,
    initialTab: 'genre',
  });

  const { selectedDate, handleConfirm } = useDateSelect();
  const dateParam = selectedDate ? toLocalDateString(selectedDate) : undefined;

  const { data } = useRecommendationArchive({ date: dateParam });

  return (
    <div className='flex-1 min-h-screen'>
      <ArchiveBanner variant='main' />
      <ArchiveNavigator
        tab={tab as ArchiveTab}
        tabs={tabs}
        onChangeTab={(nextTab) => changeTab(nextTab)}
      />
      <ArchiveListWidget
        groups={data?.groups ?? []}
        selectedDate={selectedDate ?? null}
        onDateConfirm={handleConfirm}
      />
    </div>
  );
};

export default ArchivePage;
