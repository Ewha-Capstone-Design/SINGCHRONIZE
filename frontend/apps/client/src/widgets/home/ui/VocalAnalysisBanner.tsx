'use client';

import Image from 'next/image';
import { cn } from '@/shared/lib/cn';
import { Button } from '@singchronize/ui';
import { ImgMainTitle } from '@/shared/assets/images';
import imgHomeBanner from '@/shared/assets/images/img_home_banner.jpg';
import { useNavigate } from '@/shared/lib/navigation';

const VocalAnalysisBanner = () => {
  const { go, ROUTES } = useNavigate();

  return (
    <section className={cn('relative overflow-hidden rounded-10')}>
      <Image
        src={imgHomeBanner}
        alt='When Your Voice Finds Its Song'
        aria-hidden='true'
        fill
        priority
        className='object-cover object-bottom'
      />
      <div className='absolute inset-0 bg-black/60' />

      <div className='relative z-10 px-24 flex flex-col items-center justify-center gap-7 w-full h-76'>
        <ImgMainTitle />
        <Button variant={'primary'} onClick={() => go(ROUTES.recommend)}>
          보컬 분석 받아보기
        </Button>
      </div>
    </section>
  );
};

export default VocalAnalysisBanner;
