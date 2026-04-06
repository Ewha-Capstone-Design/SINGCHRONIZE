'use client';

import { useEffect } from 'react';
import { tokenStore } from '@/shared/api/tokenStore';
import { useNavigate } from '@/shared/lib/navigation';

const Page = () => {
  const { go, ROUTES } = useNavigate();

  useEffect(() => {
    const hasAccess = Boolean(tokenStore.getAccess());
    const hasRefresh = Boolean(tokenStore.getRefresh());

    if (hasAccess || hasRefresh) {
      go(ROUTES.home, { replace: true });
    } else {
      go(ROUTES.login.root, { replace: true });
    }
  }, [go, ROUTES]);

  return null;
};

export default Page;
