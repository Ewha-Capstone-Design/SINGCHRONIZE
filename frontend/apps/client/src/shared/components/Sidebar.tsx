'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '../lib/cn';
import { SIDEBAR_ITEMS } from '../constants/sidebar';
import { IcLogo } from '../assets/icons';
import { ROUTES } from '../constants/routes';

const HIDE_SIDEBAR_PATHS = [
  ROUTES.login.root,
  ROUTES.recommend.analyze,
  ROUTES.recommend.result,
  ROUTES.live.room,
];

const Sidebar = () => {
  const pathname = usePathname();

  const shouldHideSidebar = HIDE_SIDEBAR_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`)
  );

  if (shouldHideSidebar) return null;

  return (
    <aside className='flex flex-col gap-8 w-fit h-screen bg-black p-7'>
      <IcLogo width={46} height={48} />

      <nav className='flex flex-col gap-3'>
        {SIDEBAR_ITEMS.map((item) => {
          const isRoot = item.href === '/home';
          const isActive = isRoot
            ? pathname === '/home'
            : pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                'group flex items-center gap-3 w-47 h-12 rounded-10 px-3 py-2 transition-all duration-200',
                isActive
                  ? 'bg-yellow-500-30 text-brand'
                  : 'text-gray-300 hover:bg-white-20 hover:text-gray-100 active:bg-white-10 active:text-gray-500'
              )}
            >
              <item.Icon
                className={cn(
                  'size-8 transition-colors',
                  isActive
                    ? 'text-brand'
                    : 'text-gray-300 group-hover:text-gray-100 group-active:text-gray-500'
                )}
              />
              <span className='typo-16m'>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
};

export default Sidebar;
