'use client';

import { cn } from '@/shared/lib/cn';
import { useNavigate } from '@/shared/lib/navigation';

type HomeHeaderProps = {
  username?: string | null;
  profileImageUrl?: string | null;
  className?: string;
};

export const HomeHeader = ({
  username = '프로필',
  profileImageUrl,
  className,
}: HomeHeaderProps) => {
  const { go, ROUTES } = useNavigate();

  return (
    <header
      className={cn('px-9 flex items-center justify-between w-full h-27', className)}
    >
      <h1 className='typo-28b text-white'>{username}님 반가워요 오늘도 노래해요!</h1>

      <div className='flex items-center gap-1'>
        <button
          type='button'
          onClick={() => go(ROUTES.my.root)}
          className='size-12 overflow-hidden rounded-full bg-gray-800'
          aria-label='profile'
        >
          {profileImageUrl ? (
            <img
              src={profileImageUrl}
              alt={`${username} 프로필 이미지`}
              className='size-full object-cover'
              loading='lazy'
              referrerPolicy='no-referrer'
            />
          ) : (
            <div className='size-full bg-white-10' />
          )}
        </button>
      </div>
    </header>
  );
};

export default HomeHeader;
