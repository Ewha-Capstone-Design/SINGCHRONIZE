'use client';

import { cn } from '@/shared/lib/cn';

const LibraryBanner = () => {
  return (
    <section
      className={cn(
        'px-8 py-14 flex flex-col justify-center w-full h-56.25 bg-linear-to-b from-yellow-900/50 to-bg'
      )}
    >
      <div className='flex flex-col gap-1'>
        <span className='typo-18sb text-gray-400'>노래방 키트</span>
        <h1 className='typo-32b text-white'>
          노래방에서 찜한 노래와 보컬 기록을 확인하며 노래해보세요!
        </h1>
      </div>
    </section>
  );
};

export default LibraryBanner;
