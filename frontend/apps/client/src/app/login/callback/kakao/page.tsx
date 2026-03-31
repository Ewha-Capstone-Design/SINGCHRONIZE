'use client';

import { useKakaoLoginCallback } from '@/entities/auth';

const KakaoCallbackPage = () => {
  useKakaoLoginCallback();

  return <main className='flex min-h-screen items-center justify-center text-white' />;
};

export default KakaoCallbackPage;
