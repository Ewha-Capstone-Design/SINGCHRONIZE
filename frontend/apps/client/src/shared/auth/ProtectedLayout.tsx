'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { tokenStore } from '@/shared/api/tokenStore';

type ProtectedLayoutProps = {
  children: React.ReactNode;
};

const ProtectedLayout = ({ children }: ProtectedLayoutProps) => {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const hasAccess = Boolean(tokenStore.getAccess());
    const hasRefresh = Boolean(tokenStore.getRefresh());

    if (!hasAccess && !hasRefresh) {
      const next = encodeURIComponent(pathname);
      router.replace(`/login?next=${next}`);
      return;
    }

    setReady(true);
  }, [pathname, router]);

  if (!ready) return null;

  return <>{children}</>;
};

export default ProtectedLayout;
