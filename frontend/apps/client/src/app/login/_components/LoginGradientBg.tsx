'use client';

import { usePathname } from 'next/navigation';
import { cn } from '@/shared/lib/cn';

const GRADIENT_TOP = 'bg-position-[50%_-50%]';
const GRADIENT_LOWER = 'bg-position-[50%_-90%]';

const LoginGradientBg = () => {
  const pathname = usePathname();
  const isTopGradientPage = pathname === '/login' || pathname === '/login/complete';

  return (
    <div
      className={cn(
        'pointer-events-none absolute inset-0 overflow-hidden',
        'bg-bg bg-no-repeat',
        'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.20)_0%,rgba(22,22,22,0.20)_100%)]',
        'bg-size-[120%_150%]',
        isTopGradientPage ? GRADIENT_TOP : GRADIENT_LOWER
      )}
    />
  );
};

export default LoginGradientBg;
