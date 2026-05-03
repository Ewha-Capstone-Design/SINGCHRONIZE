'use client';

import { Button } from '@singchronize/ui';
import { cn } from '@/shared/lib/cn';
import { AppImage, BaseModal } from '@/shared/components';

type HostLiveEndModalProps = {
  onClose: () => void;
  onConfirm: () => void;
  thumbnail?: string;
  isPending?: boolean;
};

export const HostLiveEndModal = ({
  onClose,
  onConfirm,
  thumbnail,
  isPending = false,
}: HostLiveEndModalProps) => {
  return (
    <BaseModal
      onClose={isPending ? () => {} : onClose}
      className={cn(
        'relative p-10 flex flex-col justify-center items-center w-full max-w-198 max-h-178 h-[70vh] rounded-20',
        'bg-bg bg-[radial-gradient(50%_50%_at_50%_50%,rgba(240,48,58,0.17)_0%,rgba(22,22,22,0.17)_100%)]',
        'bg-size-[80%_280%] bg-position-[50%_0%]',
      )}
    >
      <div className='flex flex-col gap-9 w-103'>
        <h2 className='typo-32b text-white text-center'>라이브 버스킹을 종료할까요?</h2>

        <div className='relative w-full aspect-video rounded-10 overflow-hidden bg-gray-700'>
          <AppImage
            src={thumbnail}
            alt='busking thumbnail'
            fill
            className='object-cover'
          />
        </div>

        <ul className='self-center flex flex-col'>
          <li className='typo-16r text-gray-200 before:content-["•"] before:mr-2'>
            라이브를 종료하면 방송이 즉시 종료됩니다.
          </li>
          <li className='typo-16r text-gray-200 before:content-["•"] before:mr-2'>
            종료된 방송은 다시 이어서 진행할 수 없습니다.
          </li>
        </ul>
      </div>

      <Button
        variant={'accent'}
        className='mt-[6vh]'
        onClick={onConfirm}
        disabled={isPending}
      >
        라이브 버스킹 종료 후 리포트 받기
      </Button>
    </BaseModal>
  );
};

type ViewerLiveEndModalProps = {
  onConfirm: () => void;
  isPending?: boolean;
};

export const ViewerLiveEndModal = ({
  onConfirm,
  isPending = false,
}: ViewerLiveEndModalProps) => {
  return (
    <BaseModal
      onClose={isPending ? () => {} : onConfirm}
      className={cn(
        'relative p-10 flex flex-col justify-center items-center w-full max-w-198 max-h-178 h-[70vh] rounded-20',
        'bg-bg bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.15)_0%,rgba(22,22,22,0.17)_100%)]',
        'bg-size-[130%_280%] bg-position-[50%_0%]',
      )}
    >
      <div className='flex flex-col gap-9 items-center'>
        <h2 className='typo-32b text-white text-center'>라이브가 종료되었습니다</h2>
        <p className='typo-16r text-gray-200 text-center'>버스킹이 종료되었습니다.</p>
      </div>

      <Button
        variant='accent'
        className='mt-[6vh]'
        onClick={onConfirm}
        disabled={isPending}
      >
        버스킹 목록으로 돌아가기
      </Button>
    </BaseModal>
  );
};
