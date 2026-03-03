'use client';

import { useNavigate } from '@/shared/lib/navigation';
import { IcLogo } from '@/shared/assets/icons';
import { OnboardingArtistSelect } from '@/widgets/favorite-artists/ui';

const TastePage = () => {
  const { go, ROUTES } = useNavigate();

  return (
    <main className='flex flex-col gap-10 text-white'>
      <div className='flex flex-col items-center gap-8'>
        <IcLogo />
        <h1 className='typo-32b text-center'>즐겨 부르는 가수를 선택해주세요</h1>
      </div>
      <OnboardingArtistSelect onCompleted={() => go(ROUTES.login.complete)} />
    </main>
  );
};

export default TastePage;
