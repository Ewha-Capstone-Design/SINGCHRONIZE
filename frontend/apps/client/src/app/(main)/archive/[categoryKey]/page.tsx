'use client';

import { useParams } from 'next/navigation';
import { ArchiveBanner, ArchiveListWidget } from '@/widgets/archive/ui';
import { getCategory, getCategoryApiParam } from '@/shared/constants/category';
import { useDateSelect } from '@/shared/hooks';
import { toLocalDateString } from '@/shared/lib/formatTime';

import { useRecommendationArchive } from '@/entities/archive';

const ArchiveDetailPage = () => {
  const params = useParams();
  const category = getCategory(params.categoryKey as string);

  const { selectedDate, handleConfirm } = useDateSelect();
  const dateParam = selectedDate ? toLocalDateString(selectedDate) : undefined;

  const { data } = useRecommendationArchive(
    category
      ? { ...getCategoryApiParam(category), date: dateParam }
      : { date: dateParam },
  );

  if (!category) return null;

  return (
    <div className='flex-1 min-h-screen'>
      <ArchiveBanner variant='detail' category={category} />
      <ArchiveListWidget
        groups={data?.groups ?? []}
        selectedDate={selectedDate ?? null}
        onDateConfirm={handleConfirm}
        isDetail
      />
    </div>
  );
};

export default ArchiveDetailPage;
