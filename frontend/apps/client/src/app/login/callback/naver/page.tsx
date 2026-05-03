'use client';

import { useNaverLoginCallback } from '@/entities/auth';

const NaverCallbackPage = () => {
  useNaverLoginCallback();

  return <main className='flex min-h-screen items-center justify-center text-white' />;
};

export default NaverCallbackPage;
