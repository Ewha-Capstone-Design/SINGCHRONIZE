'use client';

import { useRouter } from 'next/navigation';
import { cn } from '@/shared/lib/cn';
import { SituationCard, GenreCard } from '@/shared/components';
import { IcBack } from '@/shared/assets/icons';
import { CategoryMetaType } from '@/shared/types/category';

type ArchiveBannerProps = {
  variant: 'main' | 'detail';
  category?: CategoryMetaType;
};

const ArchiveBanner = ({ variant, category }: ArchiveBannerProps) => {
  const router = useRouter();
  const isDetail = variant === 'detail';

  const handleBack = () => {
    router.back();
  };

  const getTitle = () => {
    if (!isDetail || !category) return '지금까지 추천받은 노래들을 한 번에 확인해보세요!';
    return category.label;
  };

  return (
    <section
      className={cn(
        'relative w-full flex flex-col px-8 bg-linear-to-b from-yellow-900/50 to-bg',
        isDetail ? 'py-10 pb-14 gap-7' : 'py-14'
      )}
    >
      {isDetail && (
        <button className='w-fit' onClick={handleBack}>
          <IcBack />
        </button>
      )}

      <div className='flex items-end gap-7'>
        {isDetail && category && (
          <div className='pointer-events-none'>
            {category.type === 'situation' ? (
              <SituationCard situationKey={category.key} />
            ) : (
              <GenreCard genreKey={category.key} />
            )}
          </div>
        )}

        <div className='flex flex-col gap-1'>
          <span className='typo-18sb text-gray-400'>아카이브</span>
          <h1 className='typo-32b text-white'>{getTitle()}</h1>
        </div>
      </div>
    </section>
  );
};

export default ArchiveBanner;
