'use client';

import { useNavigate } from '@/shared/lib/navigation';
import { IcLogo } from '@/shared/assets/icons';
import { SocialLoginButton } from './_components';

const LoginPage = () => {
  const { go, ROUTES } = useNavigate();

  // TODO: 임시 라우팅 코드, 추후 'use client' 삭제 필요
  const handleKakaoLogin = () => {
    go(ROUTES.login.profile);
  };

  const handleNaverLogin = () => {
    go(ROUTES.login.profile);
  };

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
        <SocialLoginButton provider='kakao' onClick={handleKakaoLogin} />
        <SocialLoginButton provider='naver' onClick={handleNaverLogin} />
      </div>
    </main>
  );
};

export default LoginPage;
