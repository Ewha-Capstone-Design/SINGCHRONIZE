'use client';

import { useNavigate } from '@/shared/lib/navigation';
import { IcLogo } from '@/shared/assets/icons';
import { Button } from '@singchronize/ui';

const CompletePage = () => {
  const { go, ROUTES } = useNavigate();

  return (
    <div className='flex justify-center items-center'>
      <main className='flex flex-col items-center justify-between gap-18'>
        <div className='flex flex-col items-center gap-8'>
          <IcLogo />
          <h1 className='typo-38b text-center text-white'>
            회원가입을 완료했어요
            <br />
            지금 로그인하고 시작해보세요!
          </h1>
        </div>

        <div className='flex gap-3'>
          <Button variant={'outline'}>나중에 이용하기</Button>
          <Button onClick={() => go(ROUTES.home)}>홈으로 이동하기</Button>
        </div>
      </main>
    </div>
  );
};

export default CompletePage;
