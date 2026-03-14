import { Button } from '@singchronize/ui';
import { IcKakao, IcNaver } from '@/shared/assets/icons';
import type { SnsAccountUiType } from '@/entities/user/model/types';

const SNS_CONFIG = {
  kakao: { icon: <IcKakao />, label: '카카오 로그인' },
  naver: { icon: <IcNaver />, label: '네이버 로그인' },
} as const;

interface SnsAccountItemProps {
  provider: SnsAccountUiType['provider'];
  email?: string;
  connected: boolean;
  onConnect?: () => void;
}

const SnsAccountItem = ({
  provider,
  email,
  connected,
  onConnect,
}: SnsAccountItemProps) => {
  const { icon, label } = SNS_CONFIG[provider];

  return (
    <div className='px-6 py-5 flex justify-between rounded-10 border border-gray-600 bg-gray-900'>
      <div className='flex flex-1 items-center gap-3 min-w-0'>
        <div className='shrink-0'>{icon}</div>
        <div className='flex flex-col w-full overflow-hidden'>
          <p className='typo-14r text-gray-300'>{label}</p>
          <p className='typo-14r text-gray-500 truncate'>
            {connected ? email : '연동되지 않음'}
          </p>
        </div>
      </div>
      {connected ? (
        <span className='typo-16r text-gray-500 shrink-0'>연동됨</span>
      ) : (
        <Button variant='normal' size={'medium'} onClick={onConnect}>
          연동하기
        </Button>
      )}
    </div>
  );
};

export default SnsAccountItem;
