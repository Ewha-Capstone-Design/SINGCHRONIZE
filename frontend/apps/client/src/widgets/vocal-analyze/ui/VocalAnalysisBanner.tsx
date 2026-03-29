'use client';

import Image from 'next/image';
import { cn } from '@/shared/lib/cn';
import { Button } from '@singchronize/ui';
import { ImgMainTitle, ImgHomeBanner } from '@/shared/assets/images';
import { useNavigate } from '@/shared/lib/navigation';

type BannerSize = 'home' | 'recommend';

const bannerStyle: Record<
  BannerSize,
  {
    content: string;
    title: string;
    section?: string;
  }
> = {
  home: {
    content: 'pt-16 gap-10 h-72',
    title: 'w-126',
  },
  recommend: {
    content: 'pt-42 gap-18 h-[30rem]',
    title: 'w-158',
  },
};

type VocalAnalysisBannerProps = {
  size?: BannerSize;
  className?: string;
};

const VocalAnalysisBanner = ({ size = 'home', className }: VocalAnalysisBannerProps) => {
  const { go, ROUTES } = useNavigate();
  const s = bannerStyle[size];

  return (
    <section className={cn('relative overflow-hidden rounded-10', s.section, className)}>
      <Image
        src={ImgHomeBanner}
        alt='When Your Voice Finds Its Song'
        aria-hidden='true'
        fill
        priority
        className='object-cover object-top'
      />

      <div className={cn('relative z-10 flex flex-col items-center w-full', s.content)}>
        <ImgMainTitle className={s.title} />
        <Button variant='primary' onClick={() => go(ROUTES.recommend.analyze)}>
          보컬 분석 받아보기
        </Button>
      </div>
    </section>
  );
};

export default VocalAnalysisBanner;
