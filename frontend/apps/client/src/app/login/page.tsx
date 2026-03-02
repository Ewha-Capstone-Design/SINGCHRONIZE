'use client';

import { IcLogo } from '@/shared/assets/icons';
import { SocialLoginButton } from './_components';

const LoginPage = () => {
  return (
    <main className='mt-35 flex flex-col items-center justify-between w-105 h-124.25'>
      <div className='flex flex-col items-center gap-8'>
        <IcLogo />
        <h1 className='typo-38b text-center text-white'>
          환영합니다
          <br />
          간편하게 시작해보세요
        </h1>
      </div>

      <div className='flex flex-col gap-4'>
        <SocialLoginButton provider='kakao' onClick={() => {}} />
        <SocialLoginButton provider='naver' onClick={() => {}} />
      </div>
    </main>
  );
};

export default LoginPage;
