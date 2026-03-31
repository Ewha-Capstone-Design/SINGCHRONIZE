'use client';

import { IcLogo } from '@/shared/assets/icons';
import { SocialLoginButton } from './_components';
import { loginWithKakao, loginWithNaver } from '@/entities/auth/api/socialAuth';

const LoginPage = () => {
  return (
    <main className='flex flex-col items-center gap-34'>
      <div className='flex flex-col items-center gap-8'>
        <IcLogo />
        <h1 className='typo-38b text-center text-white'>
          환영합니다
          <br />
          간편하게 시작해보세요
        </h1>
      </div>

      <div className='flex flex-col gap-4'>
        <SocialLoginButton provider='kakao' onClick={loginWithKakao} />
        <SocialLoginButton provider='naver' onClick={loginWithNaver} />
      </div>
    </main>
  );
};

export default LoginPage;
