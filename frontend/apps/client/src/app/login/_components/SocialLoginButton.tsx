'use client';

import { cn } from '@/shared/lib/cn';
import { Button } from '@singchronize/ui';
import { IcKakao, IcNaver } from '@/shared/assets/icons';

type Provider = 'kakao' | 'naver';

type SocialLoginButtonProps = {
  provider: Provider;
  onClick?: () => void;
};

const PROVIDER_META: Record<Provider, { label: string; icon: React.ReactNode }> = {
  kakao: {
    label: '카카오로 시작하기',
    icon: <IcKakao />,
  },
  naver: {
    label: '네이버로 시작하기',
    icon: <IcNaver />,
  },
};

const SocialLoginButton = ({ provider, onClick }: SocialLoginButtonProps) => {
  const { label, icon } = PROVIDER_META[provider];
  return (
    <Button
      variant={'outline'}
      onClick={onClick}
      className='px-9 py-4.5 w-105 border-gray-400 gap-2'
    >
      <span
        className={cn('inline-flex h-8 w-8 items-center justify-center rounded-full')}
      >
        {icon}
      </span>
      <span className='typo-20sb text-gray-100'>{label}</span>
    </Button>
  );
};

export default SocialLoginButton;
