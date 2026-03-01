'use client';

import { useParams } from 'next/navigation';
import { ArchiveBanner, ArchiveListWidget } from '@/widgets/archive/ui';
import { getCategory } from '@/shared/constants/category';
import { toArchiveSectionUi } from '@/entities/archive/model/mapper';

import { MOCK_ARCHIVE_HISTORY } from '@/entities/archive/model/mock';

const ArchiveDetailPage = () => {
  const params = useParams();
  const category = getCategory(params.categoryKey as string);

  // TODO: 쿼리 훅으로 교체
  const groups = [toArchiveSectionUi(MOCK_ARCHIVE_HISTORY)];

  if (!category) return null;

  return (
    <div className='flex-1 min-h-screen'>
      <ArchiveBanner variant='detail' category={category} />
      <ArchiveListWidget groups={groups} isDetail />
    </div>
  );
};

export default ArchiveDetailPage;
