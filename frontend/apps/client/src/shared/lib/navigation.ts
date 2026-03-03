'use client';

import { useRouter } from 'next/navigation';
import { ROUTES, route, AppRoutePaths } from '@/shared/constants/routes';

export const useNavigate = () => {
  const router = useRouter();

  const go = (
    path: AppRoutePaths | string,
    options?: { replace?: boolean; scroll?: boolean }
  ) => {
    const action = options?.replace ? router.replace : router.push;
    action(path, { scroll: options?.scroll ?? true });
  };

  return {
    go,
    back: () => router.back(),
    refresh: () => router.refresh(),
    ROUTES,
    dynamic: route,
  };
};
